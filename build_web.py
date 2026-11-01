"""Build the public web version of the FoodQ demo from the artifact source.

Adds a Firebase Firestore store so phones and the kitchen share one queue.
Paste the project's firebaseConfig into firebase-config.js; with it empty the
page falls back to running on one device (localStorage), like the artifact.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).parent
src = (ROOT / "src" / "foodq-demo.html").read_text()
out_dir = ROOT
out_dir.mkdir(exist_ok=True)

FIREBASE_STORE = r'''
function firebaseStore(cfg){
  const app=firebase.apps.length?firebase.app():firebase.initializeApp(cfg);
  const fs=firebase.firestore(app);
  const col=fs.collection("orders"),cfgRef=fs.doc("config/settings"),ctr=fs.doc("config/counter");
  let orders=[],cfgData={},ready=false,stale=false;const subs=new Set(),unsubs=[];
  const snap=()=>({orders,soldOut:cfgData.soldOut||[],cooks:cfgData.cooks||2,clockOffset:cfgData.clockOffset==null?null:cfgData.clockOffset,ready,stale});
  const emit=()=>{const s=snap();subs.forEach(f=>f(s))};
  const timer=setTimeout(()=>{stale=true;emit()},10000);
  unsubs.push(col.onSnapshot({includeMetadataChanges:true},s=>{
    orders=s.docs.map(d=>Object.assign({},d.data(),{id:d.id}));ready=true;
    if(!s.metadata.fromCache){stale=false;clearTimeout(timer)}emit();
  },()=>{stale=true;ready=true;clearTimeout(timer);emit()}));
  unsubs.push(cfgRef.onSnapshot(s=>{cfgData=s.exists?Object.assign({},s.data()):{};emit()},()=>{}));
  const maxSeen=()=>orders.reduce((m,o)=>Math.max(m,Number(o.number)||0),100);
  const nextNumber=()=>fs.runTransaction(async tx=>{const s=await tx.get(ctr);const last=(s.exists&&Number(s.data().last))||100;const n=Math.max(last,maxSeen())+1;tx.set(ctr,{last:n});return n});
  const cfgBase=()=>({soldOut:cfgData.soldOut||[],cooks:cfgData.cooks||2,clockOffset:cfgData.clockOffset==null?null:cfgData.clockOffset});
  return{mode:"db",
    subscribe(f){subs.add(f);f(snap());return()=>subs.delete(f)},
    async createOrder(o){const ord=Object.assign({},o);if(ord.status!=="reserved")ord.number=await nextNumber();const ref=col.doc();await ref.set(ord);return Object.assign({},ord,{id:ref.id})},
    async checkin(id,p){const n=await nextNumber();const patch=Object.assign({},p,{number:n});await col.doc(id).update(patch);const o=orders.find(x=>x.id===id)||{};return Object.assign({},o,patch,{id})},
    async updateOrder(id,p){await col.doc(id).update(p)},
    async setConfig(p){await cfgRef.set(Object.assign(cfgBase(),p))},
    async reset(){const ids=orders.map(o=>o.id);for(let i=0;i<ids.length;i+=400){const b=fs.batch();ids.slice(i,i+400).forEach(id=>b.delete(col.doc(id)));await b.commit()}await ctr.set({last:100});await cfgRef.set(Object.assign(cfgBase(),{soldOut:[]}))},
    close(){unsubs.forEach(u=>{try{u()}catch(e){}});subs.clear();clearTimeout(timer)}
  };
}
'''

INIT_OLD = '''useStore(localStore());
route();
try{'''
INIT_NEW = '''useStore(localStore());
route();
try{
  const cfg=window.FOODQ_FIREBASE_CONFIG;
  if(cfg&&cfg.projectId&&window.firebase){useStore(firebaseStore(cfg));App.views.forEach(v=>v.onData())}
}catch(e){console.error("Firebase init failed",e)}
try{'''

assert "/* ---------- app shell ---------- */" in src and INIT_OLD in src
body = src.replace("/* ---------- app shell ---------- */", FIREBASE_STORE + "\n/* ---------- app shell ---------- */", 1)
body = body.replace(INIT_OLD, INIT_NEW, 1)
body = body.replace("Đồng bộ trực tuyến giữa các thiết bị", "Đồng bộ trực tuyến", 1)

FB = "10.12.2"
head_scripts = (
    f'<script src="https://www.gstatic.com/firebasejs/{FB}/firebase-app-compat.js"></script>\n'
    f'<script src="https://www.gstatic.com/firebasejs/{FB}/firebase-firestore-compat.js"></script>\n'
    '<script src="firebase-config.js"></script>\n'
)
def page(title, content):
    return ('<!doctype html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f'<title>{title}</title>\n'
            '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            + head_scripts + '</head>\n<body>\n' + content + '\n</body>\n</html>\n')

# Kitchen + presenter page: the full demo (home, App Bếp, side by side).
# Not linked from anywhere in the student app; share it with the canteen and the team only.
KITCHEN_FILE = "bep.html"
full = body.replace('href="#client" data-r="client"', 'href="./" data-r="client"', 1)
full = full.replace("'<a class=\"pick\" href=\"#client\">", "'<a class=\"pick\" href=\"./\">", 1)
(out_dir / KITCHEN_FILE).write_text(page("FoodQ – Bếp", full))

# Student page (index.html): only the student app. The header nav, the home
# screen and the whole kitchen app are removed from the code, and the hash is
# ignored, so #kitchen or #both on this address still shows the student app.
client = body
client = re.sub(r'\s*<nav class="nav".*?</nav>', '', client, count=1, flags=re.S)
client = client.replace('<a class="brand" href="#"><i>Q</i>FoodQ</a>', '<span class="brand"><i>Q</i>FoodQ</span>', 1)
k0 = client.index("/* ---------- kitchen app ---------- */")
k1 = client.index("/* ---------- routing ---------- */")
client = client[:k0] + client[k1:]
ROUTE_NEW = '''function route(){
  App.views.clear();
  document.body.classList.add("client-only");
  const note=App.notice?'<div class="notice">'+esc(App.notice)+'</div>':"";
  main.innerHTML=note+'<div class="solo-client"><div class="phone" id="cv"></div></div>';
  App.views.add(ClientView(document.getElementById("cv")));
}
window.addEventListener("hashchange",route);'''
client, n = re.subn(r'function route\(\)\{.*?\n\}\nwindow\.addEventListener\("hashchange",route\);', lambda m: ROUTE_NEW, client, count=1, flags=re.S)
assert n == 1
for a, b in [("Tên hiển thị cho bếp", "Tên của bạn (để gọi khi nhận món)"),
             ('"bếp làm ~"+mmss(q.avg)+"/đơn"', '"trung bình ~"+mmss(q.avg)+" mỗi đơn"')]:
    assert a in client, a
    client = client.replace(a, b, 1)
for bad in ("KitchenView", "#kitchen", "#both", "App Bếp", "Đặt giờ hệ thống", KITCHEN_FILE):
    assert bad not in client, bad
html = page("FoodQ – Đặt món căn tin", client)
(out_dir / "index.html").write_text(html)

cfg = out_dir / "firebase-config.js"
if not cfg.exists():
    cfg.write_text("// Dán firebaseConfig của project Firebase vào đây. Để null thì demo chạy riêng trên từng máy.\n"
                   "window.FOODQ_FIREBASE_CONFIG = null;\n")
print("built", len(html))
