const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const multer = require('multer');
const sqlite3 = require('sqlite3').verbose();
const axios = require('axios');
const { RateLimiterMemory } = require('rate-limiter-flexible');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 30000;

// 熔断配置: 每10分钟最多10次
const rateLimiter = new RateLimiterMemory({
  keyPrefix: 'bazi_api',
  points: 10,
  duration: 600, // 10分钟 = 600秒
});

// 中间件
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static(__dirname));

// 数据库
const db = new sqlite3.Database('./fortune.db');
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    birth_year INTEGER,
    birth_month INTEGER,
    birth_day INTEGER,
    birth_hour INTEGER,
    birth_place TEXT,
    life_story TEXT,
    hand_image TEXT,
    face_image TEXT,
    bazi_result TEXT,
    analysis TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);
});

// 八字计算算法
function calculateBazi(year, month, day, hour) {
  const tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
  const dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
  
  // 年柱
  const yearGan = tiangan[(year - 4) % 10];
  const yearZhi = dizhi[(year - 4) % 12];
  
  // 月柱 (简化计算)
  const monthGanIndex = ((year - 4) % 5) * 2 + ((month + 1) % 12 + 10) % 12;
  const monthGan = tiangan[monthGanIndex % 10];
  const monthZhi = dizhi[(month + 1) % 12];
  
  // 日柱 (简化计算)
  const baseDate = new Date(1900, 0, 31);
  const targetDate = new Date(year, month - 1, day);
  const diffDays = Math.floor((targetDate - baseDate) / (1000 * 60 * 60 * 24));
  const dayGan = tiangan[diffDays % 10];
  const dayZhi = dizhi[diffDays % 12];
  
  // 时柱
  const hourZhiIndex = Math.floor((hour + 1) / 2) % 12;
  const hourGanIndex = (diffDays % 5) * 2 + hourZhiIndex;
  const hourGan = tiangan[hourGanIndex % 10];
  const hourZhi = dizhi[hourZhiIndex];
  
  return {
    year: yearGan + yearZhi,
    month: monthGan + monthZhi,
    day: dayGan + dayZhi,
    hour: hourGan + hourZhi,
    full: `${yearGan}${yearZhi} ${monthGan}${monthZhi} ${dayGan}${dayZhi} ${hourGan}${hourZhi}`,
    dayGan: dayGan,
    dayZhi: dayZhi
  };
}

// 图片上传配置
const storage = multer.diskStorage({
  destination: './uploads/',
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + Math.round(Math.random() * 1E9) + path.extname(file.originalname));
  }
});
const upload = multer({ storage, limits: { fileSize: 5 * 1024 * 1024 } });

// 确保上传目录存在
if (!fs.existsSync('./uploads')) {
  fs.mkdirSync('./uploads');
}

// 调用阿里云百炼 API（使用 kimi-k2.5 兼容模式）
async function callBailianAPI(messages, retries = 2) {
  for (let i = 0; i <= retries; i++) {
    try {
      const response = await axios.post(
        'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        {
          model: 'kimi-k2.5',
          enable_thinking: true,
          messages: messages,
          max_tokens: 4000,
          temperature: 0.8
        },
        {
          headers: {
            'Authorization': 'Bearer sk-b0fc3717ed2b416db15545a416fbc9f0',
            'Content-Type': 'application/json'
          },
          timeout: 180000
        }
      );
      return response.data;
    } catch (error) {
      if (i === retries) throw error;
      console.log(`API调用失败，第${i + 1}次重试...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

// API路由
app.post('/api/analyze', upload.fields([
  { name: 'hand_image', maxCount: 1 },
  { name: 'face_image', maxCount: 1 }
]), async (req, res) => {
  try {
    // 熔断检查
    await rateLimiter.consume(req.ip, 1);
    
    const { year, month, day, hour, birth_place, life_story } = req.body;
    
    // 验证必填字段
    if (!year || !month || !day || !hour) {
      return res.status(400).json({ error: '出生时间信息不完整' });
    }
    
    // 计算八字
    const bazi = calculateBazi(parseInt(year), parseInt(month), parseInt(day), parseInt(hour));
    
    // 准备图片信息
    const handImage = req.files?.hand_image?.[0]?.filename;
    const faceImage = req.files?.face_image?.[0]?.filename;
    
    // 读取图片文件为base64
    const handImagePath = req.files?.hand_image?.[0]?.path;
    const faceImagePath = req.files?.face_image?.[0]?.path;
    let handImageBase64 = null;
    let faceImageBase64 = null;
    
    if (handImagePath && fs.existsSync(handImagePath)) {
      handImageBase64 = fs.readFileSync(handImagePath, { encoding: 'base64' });
    }
    if (faceImagePath && fs.existsSync(faceImagePath)) {
      faceImageBase64 = fs.readFileSync(faceImagePath, { encoding: 'base64' });
    }
    
    // 构建多模态消息
    let userContent = [
      { type: 'text', text: `你是融合传统命理与现代心理学的「人生叙事分析师」。请基于以下八字信息进行深度分析：

【八字信息】
年柱${bazi.year} 月柱${bazi.month} 日柱${bazi.day} 时柱${bazi.hour}
日主：${bazi.dayGan}${bazi.dayZhi} | 出生地：${birth_place || '未提供'}

${life_story ? `【人生经历】\n${life_story}` : ''}

请按以下结构输出分析：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
开篇：看见你的人生故事
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、八字解码：你的出厂设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、你的人生剧本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、关系与情感
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、事业与财富
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
五、给你的走心建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

语气像懂你多年的老朋友在深夜谈心，有温度、有洞察。总字数2000-3500字。` }
    ];
    
    // 添加手相图片
    if (handImageBase64) {
      userContent.push({
        type: 'text',
        text: '\n【手相照片】请仔细观察以下手相，分析智慧线、生命线、感情线、事业线的特征，并结合八字给出解读：'
      });
      userContent.push({
        type: 'image_url',
        image_url: { url: `data:image/jpeg;base64,${handImageBase64}` }
      });
    }
    
    // 添加面相图片
    if (faceImageBase64) {
      userContent.push({
        type: 'text',
        text: '\n【面相照片】请仔细观察以下面相，分析额头、眉毛、眼睛、鼻子、嘴巴、下巴的特征，并结合八字给出解读：'
      });
      userContent.push({
        type: 'image_url',
        image_url: { url: `data:image/jpeg;base64,${faceImageBase64}` }
      });
    }
    
    // 调用AI（多模态）
    const aiResponse = await callBailianAPI([
      { role: 'user', content: userContent }
    ]);

    const analysis = aiResponse.choices?.[0]?.message?.content || '分析生成失败';
    
    // 保存到数据库
    db.run(
      `INSERT INTO readings (birth_year, birth_month, birth_day, birth_hour, birth_place, life_story, hand_image, face_image, bazi_result, analysis) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [year, month, day, hour, birth_place, life_story, handImage, faceImage, JSON.stringify(bazi), analysis],
      function(err) {
        if (err) console.error('数据库保存失败:', err);
      }
    );

    res.json({
      success: true,
      bazi,
      analysis,
      id: this?.lastID
    });
    
  } catch (error) {
    if (error.remainingPoints !== undefined) {
      // 熔断触发
      return res.status(429).json({
        error: '系统繁忙，请稍后重试',
        retryAfter: Math.ceil(error.msBeforeNext / 1000),
        message: '每10分钟最多进行10次分析，请稍后再试'
      });
    }
    
    console.error('分析失败:', error);
    res.status(500).json({
      error: '分析过程中出现错误',
      message: error.message
    });
  }
});

// 获取历史记录
app.get('/api/history', (req, res) => {
  db.all('SELECT id, birth_year, birth_month, birth_day, birth_hour, birth_place, bazi_result, created_at FROM readings ORDER BY created_at DESC LIMIT 20', [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: '获取历史记录失败' });
    }
    res.json(rows);
  });
});

// 手相单独分析
app.post('/api/analyze-hand', upload.single('image'), async (req, res) => {
  try {
    await rateLimiter.consume(req.ip, 1);
    
    if (!req.file) {
      return res.status(400).json({ error: '请上传手相照片' });
    }
    
    const imageBase64 = fs.readFileSync(req.file.path, { encoding: 'base64' });
    
    const messages = [
      {
        role: 'user',
        content: [
          { type: 'text', text: `你是手相学专家。请仔细观察这张手相照片，分析智慧线、生命线、感情线、事业线、财运线的特征，给出详细的手相解读。

【输出要求】
1. 严禁使用Markdown符号（# * - > \`等），使用纯文本排版
2. 用「━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━」作为分隔线
3. 结构如下：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、手型总论
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、主线详解（智慧线、生命线、感情线、事业线）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、性格特质
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、运势建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. 语气像经验丰富的算命师傅，有温度有洞察
5. 总字数800-1500字` },
          { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${imageBase64}` } }
        ]
      }
    ];
    
    const aiResponse = await callBailianAPI(messages);
    const analysis = aiResponse.choices?.[0]?.message?.content || '分析生成失败';
    
    res.json({ success: true, analysis });
    
  } catch (error) {
    if (error.remainingPoints !== undefined) {
      return res.status(429).json({ error: '系统繁忙', message: '每10分钟最多10次分析' });
    }
    console.error('手相分析失败:', error);
    res.status(500).json({ error: '分析失败', message: error.message });
  }
});

// 面相单独分析
app.post('/api/analyze-face', upload.single('image'), async (req, res) => {
  try {
    await rateLimiter.consume(req.ip, 1);
    
    if (!req.file) {
      return res.status(400).json({ error: '请上传面相照片' });
    }
    
    const imageBase64 = fs.readFileSync(req.file.path, { encoding: 'base64' });
    
    const messages = [
      {
        role: 'user',
        content: [
          { type: 'text', text: `你是面相学专家。请仔细观察这张面相照片，分析额头、眉毛、眼睛、鼻子、嘴巴、下巴等五官特征，给出详细的面相解读。

【输出要求】
1. 严禁使用Markdown符号（# * - > \`等），使用纯文本排版
2. 用「━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━」作为分隔线
3. 结构如下：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、面相总论
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、五官详解（额头、眉毛、眼睛、鼻子、嘴巴、下巴）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、性格特质
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、运势建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. 语气像经验丰富的算命师傅，有温度有洞察
5. 总字数800-1500字` },
          { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${imageBase64}` } }
        ]
      }
    ];
    
    const aiResponse = await callBailianAPI(messages);
    const analysis = aiResponse.choices?.[0]?.message?.content || '分析生成失败';
    
    res.json({ success: true, analysis });
    
  } catch (error) {
    if (error.remainingPoints !== undefined) {
      return res.status(429).json({ error: '系统繁忙', message: '每10分钟最多10次分析' });
    }
    console.error('面相分析失败:', error);
    res.status(500).json({ error: '分析失败', message: error.message });
  }
});

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 根路由 - 返回首页
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// 启动服务
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🎯 八字命理分析系统启动成功`);
  console.log(`📍 访问地址: http://124.222.70.196:${PORT}`);
  console.log(`⚡ 熔断限制: 每10分钟最多10次调用`);
});
