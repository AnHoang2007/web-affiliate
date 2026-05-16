import streamlit as st
import re
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import requests
import os
from bs4 import BeautifulSoup  # <-- Thêm dòng này

# Hàm lấy thông tin ảnh và tên sản phẩm Shopee
def get_shopee_preview(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Lấy tiêu đề và ảnh từ thẻ Meta Open Graph của Shopee
            title_tag = soup.find("meta", property="og:title")
            image_tag = soup.find("meta", property="og:image")
            
            title = title_tag["content"] if title_tag else None
            image = image_tag["content"] if image_tag else None
            return title, image
    except:
        pass
    return None, None

def local_css(file_name):
    # Thêm encoding="utf-8" vào đây
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Gọi hàm để nạp giao diện từ file style.css
local_css("style.css")

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="UET Affiliate Tool", page_icon="💰", layout="centered")

# --- NẠP BIẾN MÔI TRƯỜNG ---
load_dotenv()
AT_API_KEY = os.getenv("AT_API_KEY")

class AccessTradeLinkGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Thử dùng Endpoint v2 (phiên bản mới hơn, ổn định hơn của AccessTrade)
        self.base_url = "https://api.accesstrade.vn/v1/product_links" 
        self.headers = {
            # Lưu ý: Chữ "Token" phải có dấu cách phía sau
            "Authorization": f"Token {self.api_key}", 
            "Content-Type": "application/json",
            "Accept": "application/json",  # <-- Thêm dòng này để trị dứt điểm lỗi 406
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # <-- Thêm dòng này để giả lập trình duyệt vượt tường lửa
        }

    def create_smartlink(self, original_url: str) -> str:
        payload = {"url": original_url}
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            # ĐOẠN DEBUG THẦN THÁNH:
            if response.status_code == 403:
                error_detail = response.json() # Xem server trả về lý do gì
                return f"Lỗi 403: {error_detail.get('message', 'Bạn chưa đăng ký chiến dịch này hoặc API Key sai.')}"
            
            response.raise_for_status() 
            data = response.json()
            return data.get("product_link", "Lỗi: Không tìm thấy link trong kết quả.")
            
        except requests.exceptions.HTTPError as err:
            return f"Lỗi HTTP: {err}"
        except Exception as e:
            return f"Lỗi hệ thống: {e}"

# Khởi tạo công cụ
link_generator = AccessTradeLinkGenerator(AT_API_KEY)

# --- GIAO DIỆN CHÍNH ---
st.title("🔗 Affiliate Tool Generator")
st.info("Công cụ hỗ trợ kiếm thêm thu nhập từ AccessTrade.")

with st.popover("Hướng dẫn sử dụng", use_container_width=True):
        st.markdown("""
        ### Cách làm:
        1.  Mở App Shopee(hoặc Tiktok Shop), chọn món đồ bạn muốn mua hoặc muốn giới thiệu.
        2.  Nhấn nút chia sẻ ở phía trên cùng bên phải và chọn **'Sao chép đường dẫn'**.
        3.  Quay lại đây, dán vào ô bên dưới.
        4.  Dùng link mới tạo để mua hàng.
        5.  Liên hệ zalo: 0346987464 để được nhận 80% từ tiền hoa hồng.
        """)

# Ô nhập link
url_input = st.text_input(
    "Dán link sản phẩm(Shopee hoặc Tiktok Shop) vào đây:", 
    placeholder="https://shopee.vn/... hoặc https://vt.tiktok.com")

if st.button("Tạo Link Affiliate", type="primary"):
    if url_input:
        #Danh sách các link được hỗ trợ
        valid_domains = ["shopee.vn", "shp.ee", "tiktok.com"]
        
        if any(domain in url_input for domain in valid_domains):
            with st.spinner('Đang xử lý và tạo link...'):
                clean_url = url_input
                
                short_domains = ["shp.ee", "tiktok.com"]
                if any(sd in url_input for sd in short_domains):
                    try:
                        headers_unshorten = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8"
                        }
                        res = requests.get(url_input, timeout=10, allow_redirects=True)
                        clean_url = res.url
                    except:
                        st.error("Không thể bung link rút gọn này. Hãy thử link dài nhé!")
                # Tạo link AccessTrade
                try:
                    smart_link = link_generator.create_smartlink(clean_url)

                    if "http" in smart_link:
                        st.success("Tạo link thành công! Bạn có thể copy và chia sẻ.")
                        st.code(smart_link, language="text")
                        st.link_button("Mở link mua ngay", smart_link)
                    # Kiểm tra nếu chuỗi trả về có chứa mã lỗi 502 của hệ thống
                    elif "502" in str(smart_link) or "Bad Gateway" in str(smart_link):
                        st.error("⚠️ Hệ thống AccessTrade hiện tại đang quá tải hoặc bảo trì. Bạn vui lòng quay lại sau vài phút nhé!")
                    else:
                        st.error(smart_link)
                        
                except Exception as e:
                    # Bắt lỗi dự phòng nếu hàm create_smartlink bị crash hẳn
                    st.error("⚠️ Không thể kết nối đến máy chủ đối tác. Vui lòng thử lại sau ít phút!")
        else:
            st.warning("Đây không phải link Shopee hợp lệ bạn ơi!")
    else:
        st.error("Bạn quên chưa nhập link rồi!")

# --- PHẦN CHÂN TRANG ---
st.divider()
st.caption("Phát triển bởi sinh viên UET.")