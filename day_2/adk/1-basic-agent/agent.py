from google.adk.agents import Agent

model="gemini-2.0-flash"

# ทำสร้าง Function เพื่อให้ AI นำไปเรียกใช้งาน
def find_menu_items(description: str):
    """ค้นหารายการอาหารจากคำอธิบาย เช่น ประเภทอาหาร ชื่อเมนู วัตถุดิบ หรือสไตล์

    Args:
        description: คำอธิบายประเภทอาหาร เช่น อาหารญี่ปุ่น เผ็ด ไม่ใส่เนื้อ หรือชื่อเมนู
    """
    return ["ราเมนหมูชาชู", "ข้าวหน้าปลาแซลมอน", "ซูชิปลาทูน่า"]


def get_reservation_slots(date: str):
    """ดูเวลาที่สามารถจองโต๊ะได้ในร้านนั้น

    Args:
        date: วันที่ต้องการจอง (รูปแบบ MM-DD)
    """
    return ["17:00", "18:30", "20:00"]

def add_to_cart(menu: str):
    """เพิ่มเมนูอาหารลงในรายการสั่ง
    Args:
        menu: รายการอาหาร
    """
    return "OK"

#สร้าง Agent พร้อมกำหนดการทำงานของ Agent
root_agent = Agent(
    name="neko_restaurant_agent",
    model=model,
    description="Neko restaurant agent",
    instruction="""
    คุณคือผู้ช่วยร้านอาหารชื่อ 'เนโกะ' 🐱
    คุณพูดจาน่ารัก สุภาพ ใช้คำลงท้ายว่า 'เมี๊ยว~'
    หน้าที่ของคุณคือช่วยลูกค้าร้านหาร
    เมื่อลูกค้าถามถึงเมนู ให้ดููข้อมูลจากระบบเพื่อตอบ ถ้าไม่รู้ ให้ตอบอย่างสุภาพว่าไม่รู้
    เมื่อลูกค้าต้องการของคิว เช็กคิวว่างจากระบบเพื่อจองโต๊ะให้ลูกค้า ถ้าไม่รู้ว่ามีคิวว่าเวลาไหนบ้าง ให้ตอบอย่างสุภาพว่าไม่รู้
    """,
    tools=[find_menu_items, get_reservation_slots, add_to_cart],
)




#ติดตั้ง Lib  กับ พิมใน open inte พิม adk web เเล้วกด makepublic