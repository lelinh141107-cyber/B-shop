import os, json, sqlite3, html, socket
import resend
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from email.message import EmailMessage
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
STATIC = BASE / 'static'
DB_PATH = BASE / 'data' / 'orders.db'
ENV_PATH = BASE / '.env'


def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v=line.split('=',1)
            k=k.strip(); v=v.strip().strip('"').strip("'")
            os.environ.setdefault(k,v)
load_env()

PORT = int(os.getenv('PORT','5000'))
SHOP_EMAIL = os.getenv('SHOP_EMAIL','lelinh141107@gmail.com').strip()

PRODUCTS = [
 ('avocado-plush','Gấu bơ mềm mại _(HẾT HÀNG)_','Gấu bơ','4000','avocado_plush.svg','Đồ chơi ôm mềm, đáng yêu, phù hợp làm quà cho bé.'),
 ('animal-puzzle','Xếp hình con vật _(HẾT HÀNG)_','Xếp hình','3000','animal_puzzle.svg','Bộ ghép hình con vật giúp bé luyện quan sát và tư duy.'),
 ('building-blocks','Bộ xếp hình xây dựng','Xếp hình','6000','building_blocks.jpg','Bộ khối màu nhiều kiểu để bé tự sáng tạo.'),
 ('car-track','Đường đua ô tô mini _(HẾT HÀNG)_','Xe đồ chơi','5000','car_track.svg','Đường đua mini vui nhộn cho những giờ chơi tại nhà.'),
 ('doctor-set','Bộ đồ chơi bác sĩ _(HẾT HÀNG)_','Nhập vai','5000','doctor_set.svg','Bộ dụng cụ bác sĩ đồ chơi cho bé chơi nhập vai.'),
 ('doodle-notebook','Sổ vẽ thần kỳ','Vẽ & sáng tạo','4000','doodle_notebook.jpg','Sổ nhỏ gọn để bé vẽ, tô màu và thỏa sức sáng tạo.'),
 ('fishing-game','Trò câu cá nam châm','Trò chơi','5000','fishing_game.jpg','Trò câu cá đơn giản, vui và dễ chơi cùng gia đình.'),
 ('magic-drawing','Bảng vẽ xóa được','Vẽ & sáng tạo','6000','magic_drawing.jpg','Bảng vẽ có thể xóa và dùng lại nhiều lần.'),
 ('magnetic-tiles','Gạch nam châm_(HẾT HÀNG)_','Xếp hình','5000','magnetic_tiles.svg','Các miếng ghép nam châm để bé tạo nhiều mô hình.'),
 ('monkey-target','Khỉ ném vòng','Trò chơi','4000','monkey_target.jpg','Trò chơi vận động nhẹ, tạo không khí vui vẻ.'),
 ('music-microphone','Micro đồ chơi_(HẾT HÀNG)_','Âm nhạc','5000','music_microphone.svg','Micro đồ chơi cho bé hát và biểu diễn.'),
 ('pirate-barrel','Thùng hải tặc','Trò chơi','4000','pirate_barrel.jpg','Trò chơi phản xạ vui nhộn với chủ đề hải tặc.'),
 ('pop-toys','Đồ chơi pop','Trò chơi','3000','pop_toys.jpg','Đồ chơi bóp pop nhiều màu, dễ mang theo.'),
 ('ring-game','Đèn pin chiếu hình','Trò chơi','3000','ring_game.jpg','Trò chơi ném vòng giúp bé vận động và luyện khéo léo.'),
 ('rocket-kit','Bộ tên lửa mini','Khám phá','5000','rocket_kit.jpg','Bộ mô hình chủ đề vũ trụ cho bé khám phá.'),
 ('shark-bite','Cá mập cắn','Trò chơi','4000','shark_bite.jpg','Trò chơi phản xạ cá mập vui nhộn.'),
 ('spiderman-caps','Bộ mũ siêu anh hùng','Nhập vai','4000','spiderman_caps.jpg','Phụ kiện nhập vai chủ đề siêu anh hùng.'),
 ('tea-set','Bộ ấm trà_(HẾT HÀNG)_','Nhập vai','5000','tea_set.svg','Bộ ấm chén đồ chơi cho bé chơi bán hàng, gia đình.'),
 ('toy-airplanes','Máy bay đồ chơi','Xe đồ chơi','3000','toy_airplanes.jpg','Máy bay đồ chơi nhiều màu sắc, dễ chơi.'),
 ('toy-phone','Điện thoại đồ chơi','Nhập vai','4000','toy_phone.jpg','Điện thoại đồ chơi mô phỏng các nút bấm.'),
 ('water-gun','Súng bắn máy bay','Đồ chơi ngoài trời','2000','water_gun.jpg','Đồ chơi nước mini cho các hoạt động ngoài trời.'),
 ('wood-puzzle','Puzzle gỗ_(HẾT HÀNG)_','Xếp hình','5000','wood_puzzle.svg','Puzzle gỗ nhiều mảnh, rèn khả năng tập trung.'),
]
P = {p[0]: p for p in PRODUCTS}

def money(n):
    return f'{int(n)//1000}x.000đ'

def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB_PATH)
    con.execute('''CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, customer TEXT,
      phone TEXT, address TEXT, note TEXT, items TEXT, total INTEGER)''')
    con.commit(); return con

def page(title, body, cart_count=0):
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} - Bơ Shop 🥑</title><link rel="stylesheet" href="/static/style.css"></head><body>
<div class="top">🥑 Bơ Shop · Đồ chơi nhỏ, niềm vui to!</div>
<header><a class="brand" href="/">🥑 <span>Bơ Shop</span></a><nav><a href="/">Trang chủ</a><a href="/cart">🛒 Giỏ hàng <b class="badge">{cart_count}</b></a></nav></header>
<main>{body}</main><footer><div><b>🥑 Bơ Shop</b><br>Mẹ Nhung cho Bơ chọn đồ chơi đi!</div><div>📞 Dì Lụa - 0869518915<br>💌 {html.escape(SHOP_EMAIL)}</div></footer></body></html>'''

def get_cart(handler):
    raw=handler.headers.get('Cookie','')
    # tiny cookie session: cart stored as URL-safe JSON cookie
    import base64
    val=''
    for x in raw.split(';'):
        if x.strip().startswith('cart='): val=x.strip()[5:]
    if not val: return {}
    try: return json.loads(base64.urlsafe_b64decode(val+'===').decode())
    except: return {}

def set_cart(handler, cart):
    import base64
    data=base64.urlsafe_b64encode(json.dumps(cart,separators=(',',':')).encode()).decode().rstrip('=')
    handler.send_header('Set-Cookie', f'cart={data}; Path=/; SameSite=Lax; Max-Age=604800')

def cart_items(cart):
    out=[]; total=0
    for pid,q in cart.items():
        if pid in P:
            p=P[pid]; price=int(p[3]); q=max(1,min(int(q),20)); subtotal=price*q; total+=subtotal
            out.append((p,q,subtotal))
    return out,total

def send_order_email(order_id, customer, phone, address, note, items, total):
    api_key = os.getenv('RESEND_API_KEY', '').strip()
    receiver = os.getenv('SHOP_EMAIL', '').strip()

    if not api_key or not receiver:
        return False, 'Chưa cấu hình RESEND_API_KEY hoặc SHOP_EMAIL trên Render.'

    resend.api_key = api_key

    lines = [
        f'<h2>🥑 Bơ Shop - Đơn hàng #{order_id}</h2>',
        f'<p><b>Khách hàng:</b> {html.escape(customer)}</p>',
        f'<p><b>Số điện thoại:</b> {html.escape(phone)}</p>',
        f'<p><b>Địa chỉ:</b> {html.escape(address)}</p>',
        f'<p><b>Ghi chú:</b> {html.escape(note or "Không có")}</p>',
        '<h3>Sản phẩm:</h3><ul>'
    ]

    for p, q, sub in items:
        lines.append(
            f'<li>{html.escape(p[1])} × {q}: {sub:,}đ</li>'
        )

    lines.append(f'</ul><h3>TỔNG: {total:,}đ</h3>')

    try:
        resend.Emails.send({
            "from": "Bơ Shop <onboarding@resend.dev>",
            "to": [receiver],
            "subject": f"🥑 Bơ Shop - Đơn hàng #{order_id}",
            "html": ''.join(lines)
        })
        return True, ''
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))
    def send_html(self, text, status=200, extra=None):
        b = text.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        if extra:
            extra()
        self.end_headers()
        self.wfile.write(b)
    def redirect(self, path, cart=None):
        self.send_response(303); self.send_header('Location',path); self.send_header('Cache-Control','no-store');
        if cart is not None: set_cart(self,cart)
        self.end_headers()
    def do_GET(self):
        u=urlparse(self.path); path=u.path; cart=get_cart(self); items,total=cart_items(cart)
        if path.startswith('/static/'):
            f=STATIC / path[len('/static/'):]
            if f.exists() and f.is_file():
                data=f.read_bytes(); ext=f.suffix.lower(); mime={'.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg'}.get(ext,'application/octet-stream')
                self.send_response(200); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
            self.send_error(404); return
        if path=='/':
            cards=''.join(f'''<a class="card" href="/product/{p[0]}"><div class="pic"><img src="/static/images/{p[4]}" alt="{html.escape(p[1])}"></div><div class="cat">{html.escape(p[2])}</div><h3>{html.escape(p[1])}</h3><strong>{money(p[3])}</strong><span class="detail">Xem đồ chơi →</span></a>''' for p in PRODUCTS)
            body=f'''<section class="hero"><div><span class="pill">🥑 SHOP ĐỒ CHƠI CỦA BƠ</span><h1>Mẹ Nhung cho Bơ<br>chọn đồ chơi đi! 🧸</h1><p>Những món đồ chơi xinh xắn, dễ chọn và giá dưới 100k.</p><a class="btn" href="#shop">Xem đồ chơi</a></div><img src="/static/images/bo_avatar.png" alt="Bơ"></section><section id="shop"><div class="section-head"><div><small>GỢI Ý CHO BƠ</small><h2>Chọn món Bơ thích nhé 💚</h2></div><span>{len(PRODUCTS)} món đồ chơi</span></div><div class="grid">{cards}</div></section>'''
            self.send_html(page('Trang chủ',body,len(cart))); return
        if path.startswith('/product/'):
            pid=path.split('/')[-1]; p=P.get(pid)
            if not p: self.send_error(404); return
            body=f'''<div class="crumb"><a href="/">← Quay lại shop</a></div><section class="product"><div class="bigpic"><img src="/static/images/{p[4]}" alt="{html.escape(p[1])}"></div><div><span class="cat">{html.escape(p[2])}</span><h1>{html.escape(p[1])}</h1><div class="price">{money(p[3])}</div><p>{html.escape(p[5])}</p><form method="post" action="/cart/add"><input type="hidden" name="pid" value="{p[0]}"><label>Số lượng <input class="qty" type="number" name="qty" value="1" min="1" max="20"></label><button class="btn" type="submit">🛒 Thêm vào giỏ</button></form></div></section>'''
            self.send_html(page(p[1],body,len(cart))); return
        if path=='/cart':
            rows=''.join(f'''<div class="cartrow"><img src="/static/images/{p[4]}"><div class="grow"><b>{html.escape(p[1])}</b><small>{money(p[3])} × {q}</small></div><strong>{sub:,}đ</strong><form method="post" action="/cart/remove"><input type="hidden" name="pid" value="{p[0]}"><button class="linkbtn">Xóa</button></form></div>''' for p,q,sub in items)
            if not items: rows='<div class="empty">🧸 Giỏ hàng đang trống.<br><a href="/">Quay lại chọn đồ chơi</a></div>'
            action=f'<a class="btn wide" href="/checkout">Đặt hàng →</a>' if items else ''
            body=f'''<div class="section-head"><div><small>GIỎ HÀNG</small><h1>Đồ Bơ đã chọn 🛒</h1></div></div><section class="cartbox">{rows}</section>{f'<div class="total"><span>Tổng cộng</span><b>{total:,}đ</b></div>{action}' if items else ''}'''
            self.send_html(page('Giỏ hàng',body,len(cart))); return
        if path=='/checkout':
            if not items: self.redirect('/cart'); return
            body=f'''<div class="section-head"><div><small>ĐẶT HÀNG</small><h1>Thông tin nhận đồ 🥑</h1></div></div><div class="checkout"><form method="post" action="/checkout"><label>Họ và tên<input name="customer" required placeholder="Tên của bạn"></label><label>Số điện thoại<input name="phone" required inputmode="tel" placeholder="Số điện thoại"></label><label>Địa chỉ nhận hàng<textarea name="address" required placeholder="Số nhà, đường, phường/xã..."></textarea></label><label>Ghi chú<textarea name="note" placeholder="Ví dụ: giao giờ nào, gọi trước khi giao..."></textarea></label><div class="order-summary"><b>Tổng đơn: {total:,}đ</b><small>{len(items)} loại đồ chơi</small></div><button class="btn wide" type="submit">🥑 Xác nhận đặt hàng</button></form></div>'''
            self.send_html(page('Đặt hàng',body,len(cart))); return
        if path.startswith('/confirmation/'):
            oid=path.split('/')[-1];
            con=db(); row=con.execute('select customer,total from orders where id=?',(oid,)).fetchone(); con.close()
            if not row: self.send_error(404); return
            body=f'''<section class="success"><div class="successicon">✓</div><h1>Đặt hàng thành công!</h1><p>Cảm ơn <b>{html.escape(row[0])}</b>. Đơn hàng <b>#{oid}</b> đã được lưu.</p><div class="order-summary"><b>Tổng đơn: {row[1]:,}đ</b><small>Shop sẽ liên hệ để xác nhận đơn.</small></div><a class="btn" href="/">Tiếp tục xem đồ chơi</a></section>'''
            self.send_html(page('Đặt hàng thành công',body,0)); return
        self.send_error(404)

    def do_POST(self):
        path=urlparse(self.path).path; length=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(length).decode('utf-8','replace'); form={k:v[-1] for k,v in parse_qs(raw).items()}; cart=get_cart(self)
        if path=='/cart/add':
            pid=form.get('pid','');
            try: q=max(1,min(int(form.get('qty','1')),20))
            except: q=1
            if pid in P: cart[pid]=min(20,int(cart.get(pid,0))+q)
            self.redirect('/cart',cart); return
        if path=='/cart/remove':
            cart.pop(form.get('pid',''),None); self.redirect('/cart',cart); return
        if path=='/checkout':
            items,total=cart_items(cart)
            if not items: self.redirect('/cart'); return
            customer=form.get('customer','').strip(); phone=form.get('phone','').strip(); address=form.get('address','').strip(); note=form.get('note','').strip()
            if not customer or not phone or not address: self.send_html(page('Thiếu thông tin','<section class="success"><h1>Vui lòng điền đủ thông tin.</h1><a class="btn" href="/checkout">Quay lại</a></section>',len(cart)),400); return
            con=db(); now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'); payload=[{'name':p[1],'qty':q,'price':int(p[3])} for p,q,_ in items]
            cur=con.execute('insert into orders(created_at,customer,phone,address,note,items,total) values(?,?,?,?,?,?,?)',(now,customer,phone,address,note,json.dumps(payload,ensure_ascii=False),total)); oid=cur.lastrowid; con.commit(); con.close()
            ok,err=send_order_email(oid,customer,phone,address,note,items,total)

            if ok:
                self.redirect(f'/confirmation/{oid}',{})
            else:
                error_page = page(
                    'Lỗi gửi email',
                    f'''<section class="success">
                    <h1>Đặt hàng đã lưu nhưng chưa gửi được email</h1>
                    <p><b>Mã đơn:</b> #{oid}</p>
                    <p><b>Lỗi:</b> {html.escape(err)}</p>
                    <a class="btn" href="/">Quay lại shop</a>
                    </section>''',
                    len(cart)
                )
                self.send_html(error_page, 500)
            return
        self.send_error(404)

def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return '127.0.0.1'

if __name__=='__main__':
    db().close(); server=ThreadingHTTPServer(('0.0.0.0',PORT),Handler)
    print('='*54); print('🥑 BƠ SHOP - PURE PYTHON'); print(f'💻 Máy tính: http://127.0.0.1:{PORT}'); print(f'📱 Điện thoại cùng Wi-Fi: http://{local_ip()}:{PORT}'); print('Nhấn Ctrl+C để dừng.'); print('='*54)
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nĐã dừng Bơ Shop.'); server.server_close()
