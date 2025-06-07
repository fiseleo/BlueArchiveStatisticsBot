import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class BlueArchiveData:
    DataBaseURL = "https://schaledb.com/"
    ImageFilePath = "iconimages/"

class ImageFactory:
    @staticmethod
    def StudentUsageImageGenerator(student_info,student_usage_array:list) -> io.BytesIO:
        #預先載入icon相關圖片
        print("✅開始繪製角色使用狀態圖",flush=True)
        print("載入icon中...",flush=True)

        StarImg1 = Image.open(f"{BlueArchiveData.ImageFilePath}Common_Yellow_Star_Icon.png").resize((30,30)).convert("RGBA")
        StarImg2 = Image.open(f"{BlueArchiveData.ImageFilePath}Common_Blue_Star_Icon.png").resize((30,30)).convert("RGBA")
        arrow_img = Image.open(f"{BlueArchiveData.ImageFilePath}arrow_down.png").resize((30,30)).convert("RGBA")
        student_borrow_img = Image.open(f"{BlueArchiveData.ImageFilePath}common_icon_asist.png").resize((30,30)).convert("RGBA")
        type_attack_img = Image.open(f"{BlueArchiveData.ImageFilePath}Type_Attack.png").resize((50,50)).convert("RGBA")
        type_defense_img = Image.open(f"{BlueArchiveData.ImageFilePath}Type_Defense.png").resize((50,50)).convert("RGBA")

        attack_color = ImageFactory.StudentAttackTypeColorMatch(student_info["BulletType"])
        defense_color = ImageFactory.StudentDefenseTypeColorMatch(student_info["ArmorType"])
        base_image_size = [2800,1400]
        #以學生學園圖為背景
        print("正在繪製背景與角色圖...",flush=True)

        BaseImage:Image.Image = (Image.open(f"CollectionBG/{student_info['CollectionBG']}.jpg")).resize((base_image_size[0],base_image_size[1]))
        BaseImage = BaseImage.filter(ImageFilter.GaussianBlur(40))
        BaseImageDraw = ImageDraw.Draw(BaseImage,"RGBA")

        CardSizeX, CardSizeY = (400,452)
        CardLeftX = 100
        CardUpY = int((base_image_size[1]/2)-475)
        CardRightX,CardDownY = CardLeftX+CardSizeX,CardUpY+CardSizeY

        #分配角色圖底色與陰影
        CharacterColor = ImageFactory.CharacterRarityColorMatch(student_info["StarGrade"])
        ImageFactory.CharacterCardGenerator(BaseImageDraw,[CardLeftX,CardUpY,CardRightX,CardDownY],CharacterColor,ImageGap=(15,24))

        #繪製角色本體
        CharacterImage = Image.open(f"studentsimage/{student_info['Id']}.webp").resize((CardSizeX,CardSizeY)).convert("RGBA")
        BaseImage.paste(CharacterImage,(CardLeftX,CardUpY),CharacterImage)

        #角色卡名稱
        print("將角色名稱寫上角色圖上...",flush=True)
        CharacterName = (student_info["Name"])
        NamePreProcessList = {"（":"(","）":")"}
        for key, value in NamePreProcessList.items():
            CharacterName = CharacterName.replace(key,value)
        
        Font = Path(__file__).parent / "Font"
        
        font = ImageFont.truetype(Font/"msjhbd.ttc", 42) #微軟正黑體
        #font_title = ImageFont.truetype("msjhbd.ttc", 40) #微軟正黑體

        BaseImageDraw.rounded_rectangle([CardLeftX,CardDownY-80+5,CardRightX,CardDownY],1,(0,0,0,150))
        BaseImageDraw.text((CardLeftX+CardSizeX/2,CardDownY-24), CharacterName ,font=font,fill=(255,255,255,255),anchor="ms")

        #繪製場地適應性
        print("正在繪製場地適應性與攻防屬性...",flush=True)
        adaptation_type_list = ["Street","Outdoor","Indoor"]
        street_battle_adaptation = student_info["StreetBattleAdaptation"]
        outdoor_battle_adaptation = student_info["OutdoorBattleAdaptation"]
        indoor_battle_adaptation = student_info["IndoorBattleAdaptation"]
        adaptation_value_list = [street_battle_adaptation,outdoor_battle_adaptation,indoor_battle_adaptation]
        weapon_adaptation_type = student_info["Weapon"]["AdaptationType"]
        WeaponAdaptationValue = student_info["Weapon"]["AdaptationValue"]
        terrain_position = (CardLeftX+50,CardDownY+275)

        terrain_position_offset_x = 120
        terrain_position_offset_y = 100
        total_terrain_type_count = 3

        BaseImageDraw.rounded_rectangle([terrain_position[0]-50,terrain_position[1]-50,terrain_position[0]+(terrain_position_offset_x*total_terrain_type_count),terrain_position[1]+(terrain_position_offset_y*total_terrain_type_count)],10,(255,255,255,150))

        for terrain_index in range(0,total_terrain_type_count):
            terrain_position_dynamic_offset_x = terrain_index*terrain_position_offset_x
            terrain_position_dynamic_offset_y = terrain_position_offset_y
            terrain_name = adaptation_type_list[terrain_index]
            terrain_value = adaptation_value_list[terrain_index]
            terrain_type_img = Image.open(f"{BlueArchiveData.ImageFilePath}Terrain_{terrain_name}.png").resize((65,65)).convert("RGBA")
            ImageFactory.ColoredCircleDrawer(BaseImageDraw,terrain_type_img.size,(terrain_position[0]+terrain_position_dynamic_offset_x,terrain_position[1]),(0,0,0,150),15)
            BaseImage.paste(terrain_type_img,(terrain_position[0]+terrain_position_dynamic_offset_x,terrain_position[1]),terrain_type_img)
            
            terrain_adaptation_img = Image.open(f"{BlueArchiveData.ImageFilePath}Adaptresult{terrain_value}.png").resize((60,60)).convert("RGBA")
            BaseImage.paste(terrain_adaptation_img,(terrain_position[0]+terrain_position_dynamic_offset_x,terrain_position[1]+terrain_position_dynamic_offset_y),terrain_adaptation_img)

            if weapon_adaptation_type != terrain_name:
                continue
            
            terrain_value += WeaponAdaptationValue
            terrain_adaptation_img = Image.open(f"{BlueArchiveData.ImageFilePath}Adaptresult{terrain_value}.png").resize((60,60)).convert("RGBA")
            BaseImage.paste(terrain_adaptation_img,(terrain_position[0]+terrain_position_dynamic_offset_x,terrain_position[1]+terrain_position_dynamic_offset_y*2),terrain_adaptation_img)

        #繪製防禦與攻擊屬性
        attack_img_position = (CardLeftX+100,CardDownY+100)
        defense_img_position = (CardLeftX+250,CardDownY+100)
        
        ImageFactory.ColoredCircleDrawer(BaseImageDraw,type_attack_img.size,attack_img_position,attack_color,20)
        BaseImage.paste(type_attack_img,attack_img_position,type_attack_img)
        ImageFactory.ColoredCircleDrawer(BaseImageDraw,type_defense_img.size,defense_img_position,defense_color,20)
        BaseImage.paste(type_defense_img,defense_img_position,type_defense_img)

        #繪製名次資訊
        print("繪製名次與星數等UI資訊...",flush=True)
        data_position_array_x = [750,1050,1300,1550,1800,2050,2300,2550]
        data_position_array_y = [500,700,900,1100]
        rank_list = [1000,5000,10000,20000]
        ui_text_list_1 = ["助戰","三星以下","四星","五星未開專","專一","專二","專三"]
        ui_text_list_2 = ["1000名內","5000名內","10000名內","20000名內"]
        #繪製星數
        BaseImageDraw.rounded_rectangle([data_position_array_x[0]-150,data_position_array_y[0]-300,data_position_array_x[7]+150,data_position_array_y[3]+150],10,(255,255,255,150))
        BaseImageDraw.rounded_rectangle([data_position_array_x[0]-100,250,data_position_array_x[7]+100,400],5,(0,0,0,100))
        
        BaseImageDraw.line([(data_position_array_x[0]-100,data_position_array_y[0]-250),(data_position_array_x[1]-100,data_position_array_y[1]-300)],(255,255,255,255),5)
        BaseImageDraw.line([(data_position_array_x[0]-100,data_position_array_y[1]-300),(data_position_array_x[7]+100,data_position_array_y[1]-300)],(255,255,255,255),5)
        BaseImageDraw.line([(data_position_array_x[1]-100,data_position_array_y[0]-250),(data_position_array_x[1]-100,data_position_array_y[3]+100)],(255,255,255,255),5)

        star_count_list = [1,3,4,5,1,2,3]
        image_list = [student_borrow_img,StarImg1,StarImg1,StarImg1,StarImg2,StarImg2,StarImg2]
        BaseImage.paste(arrow_img,(data_position_array_x[2]-100+145,data_position_array_y[0]-375+188),arrow_img)
        for array_index in range(0,7):
            ImageFactory.StarImgEqualDistributed(star_count_list[array_index],BaseImage,image_list[array_index],data_position_array_x[array_index+1]-100,data_position_array_y[0]-375)

        #繪製UI文字
        for array_second_index in range(1,8):
            ui_text = ui_text_list_1[array_second_index-1]
            #BaseImageDraw.text((data_position_array_x[array_second_index],data_position_array_y[0]-125), f"{ui_text}" ,font=font,fill=(255,255,255,255),anchor="ms")
        BaseImageDraw.text((data_position_array_x[0]-25,data_position_array_y[0]-125), "名次" ,font=font,fill=(255,255,255,255),anchor="ms")
        BaseImageDraw.text((data_position_array_x[0]+120,data_position_array_y[0]-175), "練度" ,font=font,fill=(255,255,255,255),anchor="ms")
        for array_second_index in range(0,4):
            BaseImageDraw.text((data_position_array_x[0]-80,data_position_array_y[array_second_index]+25), ui_text_list_2[array_second_index] ,font=font,fill=(0,0,0,255),anchor="ls")
        #繪製數據
        print("將角色使用數據繪製至圖片上...",flush=True)
        for student_usage_array_first_index in range(0,4):
            for student_usage_array_second_index in range(1,8):
                usage_data = student_usage_array[student_usage_array_first_index][student_usage_array_second_index-1]
                usage_persentage = round((usage_data/rank_list[student_usage_array_first_index])*100,1)
                if usage_data != 0:
                    BaseImageDraw.text((data_position_array_x[student_usage_array_second_index],data_position_array_y[student_usage_array_first_index]+50), f"({usage_persentage}%)" ,font=font,fill=(0,0,0,255),anchor="ms")
                if usage_data == 0:
                    usage_data_text = "-"
                else:
                    usage_data_text = f"{usage_data}位"
                BaseImageDraw.text((data_position_array_x[student_usage_array_second_index],data_position_array_y[student_usage_array_first_index]), usage_data_text ,font=font,fill=(0,0,0,255),anchor="ms")
        
        print("✅已繪製完成角色使用狀態圖，準備輸出",flush=True)
        #儲存圖片並輸出
        base_image_bytes = io.BytesIO()
        BaseImage.save(base_image_bytes, format="PNG")
        base_image_bytes.seek(0)
        return base_image_bytes
    
    @staticmethod
    def StudentAttackTypeColorMatch(ColorType):
        match ColorType:
            case "Explosion":
                ColorCode = (167, 12, 25)
            case "Pierce":
                ColorCode = (178, 109, 31)
            case "Mystic":
                ColorCode = (33, 111, 156)
            case "Sonic":
                ColorCode = (148, 49, 165)
        return ColorCode
    
    @staticmethod
    def StudentDefenseTypeColorMatch(ColorType):
        match ColorType:
            case "LightArmor":
                ColorCode = (167, 12, 25)
            case "HeavyArmor":
                ColorCode = (178, 109, 31)
            case "Unarmed":
                ColorCode = (33, 111, 156)
            case "ElasticArmor":
                ColorCode = (148, 49, 165)
        return ColorCode
    
    @staticmethod
    def CharacterRarityColorMatch(StarGrades):
        match StarGrades:
            case 1:
                RGB_Value = (255,255,255)
            case 2:
                RGB_Value = (230,143,22)
            case 3:
                RGB_Value = (155,133,230)
        return RGB_Value
    
    @staticmethod
    def CharacterCardGenerator(
        BaseImage:ImageDraw.ImageDraw,
        CardSize:tuple[float,float,float,float],
        RarityCardColor,
        BaseCardColor=(192,192,192),
        ImageGap=(5,8)
    ):
        """
        繪製學生卡牌外框與底色
        """

        #繪製角色圖底色與陰影
        CharacterImageGap1, CharacterImageGap2 = ImageGap

        CardLeftX,CardLeftY,CardRightX,CardRightY= CardSize

        BaseImage.rounded_rectangle([
            CardLeftX-CharacterImageGap2,
            CardLeftY-CharacterImageGap2,
            CardRightX+CharacterImageGap2,
            CardRightY+CharacterImageGap2
        ],10,BaseCardColor)

        BaseImage.rounded_rectangle([
            CardLeftX-CharacterImageGap1,
            CardLeftY-CharacterImageGap1,
            CardRightX+CharacterImageGap1,
            CardRightY+CharacterImageGap1
        ],10,RarityCardColor)

    @staticmethod
    def ColoredCircleDrawer(
        BaseImageDraw:ImageDraw.ImageDraw,
        CenterImageSize:tuple[int,int],
        CenterImagePosition:tuple[int,int],
        Color:tuple[int,int,int],
        RadiusOffset:int=0
    ):
        """
        繪製一個以目標圖案為中心的圓形純色圖案
        """
        CenterImageWidge, CenterImageHeight = CenterImageSize
        CenterImagePositionX, CenterImagePositionY = CenterImagePosition

        CenterPositionX = CenterImagePositionX + CenterImageWidge/2
        CenterPositionY = CenterImagePositionY + CenterImageHeight/2
        Radius = CenterImageWidge/2+RadiusOffset
        BaseImageDraw.ellipse((CenterPositionX-Radius,CenterPositionY-Radius,CenterPositionX+Radius,CenterPositionY+Radius),fill=Color)

    @staticmethod
    def StarImgEqualDistributed(StarCount:int,Background:Image.Image,StarImg:Image.Image,x,y):
        """
        根據星星數量平均分配圖案位置
        """
        match StarCount:
            case 1:
                Background.paste(StarImg,(x+85,y+188),StarImg)
            case 2:
                Background.paste(StarImg,(x+70,y+188),StarImg)
                Background.paste(StarImg,(x+100,y+188),StarImg)
            case 3:
                Background.paste(StarImg,(x+55,y+188),StarImg)
                Background.paste(StarImg,(x+85,y+188),StarImg)
                Background.paste(StarImg,(x+115,y+188),StarImg)
            case 4:
                Background.paste(StarImg,(x+40,y+188),StarImg)
                Background.paste(StarImg,(x+70,y+188),StarImg)
                Background.paste(StarImg,(x+100,y+188),StarImg)
                Background.paste(StarImg,(x+130,y+188),StarImg)
            case 5:
                Background.paste(StarImg,(x+25,y+188),StarImg)
                Background.paste(StarImg,(x+55,y+188),StarImg)
                Background.paste(StarImg,(x+85,y+188),StarImg)
                Background.paste(StarImg,(x+115,y+188),StarImg)
                Background.paste(StarImg,(x+145,y+188),StarImg)