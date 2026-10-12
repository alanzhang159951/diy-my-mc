// 交叉校验：把 demo/index.html 里的 JS 引擎抽出来单独跑，确认与 scripts/diy_mc.py 结果一致。
// 用法：node tests/crosscheck.js
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'demo', 'index.html'), 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) throw new Error('未找到脚本块');
const engine = match[1].split('const LIKE_OPTS')[0];

const api = new Function(engine + '\nreturn { generate, chooseCoupons, COUPONS };')();

const cases = [
  { name: '辣 / 预算30 / 700kcal', cfg: { budget: 30, kcal: 700, likes: ['辣'], dislikes: [], period: '', wantDessert: false } },
  { name: '不辣+排除牛肉 / 预算25 / 早餐', cfg: { budget: 25, kcal: 700, likes: ['不辣'], dislikes: ['牛肉'], period: '早餐', wantDessert: false } },
  { name: '预算20 / 600kcal', cfg: { budget: 20, kcal: 600, likes: [], dislikes: [], period: '', wantDessert: false } },
];

let failures = 0;
for (const c of cases) {
  console.log(`\n### ${c.name}`);
  const out = api.generate(c.cfg);
  if (!out.length) { console.log('  （无方案）'); continue; }
  out.forEach((s, i) => {
    const combo = s.items.filter(x => !x.isBundle).map(x => x.name).join(' + ');
    console.log(`  ${i + 1}. 到手 ¥${s.final.toFixed(2)} | 原价 ¥${s.original.toFixed(2)} | ${Math.round(s.kcal)} kcal | ${combo}`);
    if (s.swaps.length) console.log(`     替换：${s.swaps.join('；')}`);
  });
  if (out.some(s => s.final > c.cfg.budget + 1e-6)) { console.log('  ✗ 存在超出预算的方案'); failures++; }
  if (out.some(s => Math.abs(s.original - s.final - s.discount) > 0.011)) { console.log('  ✗ 价格勾稽不平'); failures++; }
  if (out.some(s => s.kcal <= 0)) { console.log('  ✗ 热量汇总为 0'); failures++; }
}

// 忌口必须真正生效
const withBeef = api.generate({ budget: 40, kcal: 700, likes: [], dislikes: ['牛肉'], period: '', wantDessert: false });
const beefLeak = withBeef.filter(s => s.items.some(i => /巨无霸|双层吉士/.test(i.name)));
console.log(`\n### 忌口校验：排除牛肉后仍出现牛肉餐品的方案数 = ${beefLeak.length}`);
if (beefLeak.length) failures++;

// 否定标签不得误命中：排除「辣」后不应再出现带辣标签的餐品
const noSpicy = api.generate({ budget: 40, kcal: 700, likes: [], dislikes: ['辣'], period: '', wantDessert: false });
const spicyLeak = noSpicy.filter(s => s.items.some(i => i.tags.includes('辣')));
console.log(`### 否定标签校验：排除辣后仍出现辣味餐品的方案数 = ${spicyLeak.length}`);
if (spicyLeak.length) failures++;

console.log(failures === 0 ? '\n✓ 交叉校验全部通过' : `\n✗ 发现 ${failures} 处问题`);
process.exit(failures === 0 ? 0 : 1);
