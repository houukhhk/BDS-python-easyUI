import subprocess,os,sys,threading,time,json,shutil,socket,winsound,requests
from datetime import datetime
import tkinter as tk
from tkinter import ttk,scrolledtext,messagebox,filedialog,simpledialog

class OnlineServerManager:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Minecraft服务器管理器 v10.0 | 制作：houukhhk")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1a1a2e')
        self.colors={'bg_dark':'#1a1a2e','bg_medium':'#16213e','bg_light':'#0f3460','accent_green':'#00b894','accent_red':'#d63031','accent_orange':'#e17055','accent_yellow':'#fdcb6e','accent_blue':'#0984e3','accent_purple':'#6c5ce7','text_white':'#ffffff','text_gray':'#b2bec3','console_bg':'#0a0a0a'}
        self.server_process=None
        self.server_running=False
        self.start_time=None
        self.current_dir=os.path.dirname(os.path.abspath(__file__))
        self.server_exe=os.path.join(self.current_dir,"bedrock_server.exe")
        self.online_players=[]
        self.local_ip=self.get_local_ip()
        self.public_ip=self.get_public_ip()
        self.config_file=os.path.join(self.current_dir,"server_manager_config.json")
        self.load_all_configs()
        self.backup_folder=os.path.join(self.current_dir,"backups")
        self.worlds_folder=os.path.join(self.current_dir,"worlds")
        os.makedirs(self.backup_folder,exist_ok=True)
        os.makedirs(self.worlds_folder,exist_ok=True)
        self.banned_players={}
        self.setup_ui()
        self.refresh_backup_list()
        self.start_player_refresh()
        self.log_to_console("🎮 服务器管理器已启动 | 👑 制作：houukhhk")
        self.log_to_console(f"🖥️ 本机IP: {self.local_ip}")
        self.log_to_console(f"🌐 外网IP: {self.public_ip if self.public_ip else '获取失败'}")
        self.play_sound('startup')
    
    def get_public_ip(self):
        """获取外网IP地址（供好友远程连接）"""
        try:
            response=requests.get('https://api.ipify.org',timeout=5)
            if response.status_code==200:
                return response.text.strip()
        except:
            try:
                response=requests.get('https://icanhazip.com',timeout=5)
                if response.status_code==200:
                    return response.text.strip()
            except:
                pass
        return None
    
    def play_sound(self,sound_type='backup'):
        if not getattr(self,'sound_enabled',True): return
        try:
            if sound_type=='backup': winsound.Beep(880,200);winsound.Beep(988,200)
            elif sound_type=='error': winsound.Beep(440,300);winsound.Beep(330,300)
            elif sound_type=='startup': winsound.Beep(523,150);winsound.Beep(659,150);winsound.Beep(784,300)
            elif sound_type=='player_join': winsound.Beep(659,100);winsound.Beep(784,100)
            elif sound_type=='player_leave': winsound.Beep(784,100);winsound.Beep(659,100)
        except: pass
    
    def get_local_ip(self):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(("8.8.8.8",80))
            ip=s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"
    
    def load_all_configs(self):
        default_config={"server_exe":self.server_exe,"backup_enabled":False,"backup_interval":30,"keep_backups":10,"online_mode":False,"command_blocks":True,"allow_cheats":False,"sound_enabled":True,"multiplayer_settings":{"allow_friends":True,"allow_friends_of_friends":True,"visible_to_lan":True},"server_settings":{"server-name":"我的世界服务器","motd":"欢迎！","gamemode":"survival","difficulty":"normal","max-players":"20","view-distance":"10"},"disabled_commands":[],"gamerules":{"keepInventory":False,"doFireTick":True,"tntExplodes":True,"pvp":True,"doImmediateRespawn":False,"naturalRegeneration":True,"showDeathMessages":True,"doMobSpawning":True,"doWeatherCycle":True,"doDaylightCycle":True,"commandBlockOutput":True,"mobGriefing":True,"doEntityDrops":True,"doTileDrops":True,"announceAdvancements":True}}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file,'r',encoding='utf-8') as f: config=json.load(f)
                self.server_exe=config.get("server_exe",default_config["server_exe"])
                self.auto_backup_enabled=config.get("backup_enabled",default_config["backup_enabled"])
                self.backup_interval=config.get("backup_interval",default_config["backup_interval"])
                self.keep_backups=config.get("keep_backups",default_config["keep_backups"])
                self.online_mode=config.get("online_mode",default_config["online_mode"])
                self.command_blocks=config.get("command_blocks",default_config["command_blocks"])
                self.allow_cheats=config.get("allow_cheats",default_config["allow_cheats"])
                self.sound_enabled=config.get("sound_enabled",default_config["sound_enabled"])
                self.multiplayer_settings=config.get("multiplayer_settings",default_config["multiplayer_settings"])
                self.server_settings=config.get("server_settings",default_config["server_settings"])
                self.disabled_commands=set(config.get("disabled_commands",default_config["disabled_commands"]))
                self.gamerules=config.get("gamerules",default_config["gamerules"])
            except: self.use_default_config(default_config)
        else: self.use_default_config(default_config);self.save_all_configs()
    
    def use_default_config(self,dc):
        self.server_exe=dc["server_exe"]
        self.auto_backup_enabled=dc["backup_enabled"]
        self.backup_interval=dc["backup_interval"]
        self.keep_backups=dc["keep_backups"]
        self.online_mode=dc["online_mode"]
        self.command_blocks=dc["command_blocks"]
        self.allow_cheats=dc["allow_cheats"]
        self.sound_enabled=dc["sound_enabled"]
        self.multiplayer_settings=dc["multiplayer_settings"]
        self.server_settings=dc["server_settings"]
        self.disabled_commands=set(dc["disabled_commands"])
        self.gamerules=dc["gamerules"]
    
    def save_all_configs(self):
        try:
            config={"server_exe":self.server_exe,"backup_enabled":self.auto_backup_enabled,"backup_interval":self.backup_interval,"keep_backups":self.keep_backups,"online_mode":self.online_mode,"command_blocks":self.command_blocks,"allow_cheats":self.allow_cheats,"sound_enabled":self.sound_enabled,"multiplayer_settings":self.multiplayer_settings,"server_settings":self.server_settings,"disabled_commands":list(self.disabled_commands),"gamerules":self.gamerules}
            with open(self.config_file,'w',encoding='utf-8') as f: json.dump(config,f,indent=4,ensure_ascii=False)
            return True
        except: return False
    
    def setup_ui(self):
        header=tk.Frame(self.root,bg=self.colors['bg_light'],height=40)
        header.pack(fill='x',side='top')
        header.pack_propagate(False)
        tk.Label(header,text="🎮 Minecraft Server Manager",font=("微软雅黑",12,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_green']).pack(side='left',padx=15,pady=5)
        credit=tk.Frame(header,bg=self.colors['accent_purple'],relief='ridge',bd=1)
        credit.pack(side='left',padx=20,pady=5)
        tk.Label(credit,text="👑 制作：houukhhk 👑",font=("微软雅黑",11,"bold"),bg=self.colors['accent_purple'],fg='white').pack(padx=10,pady=2)
        tk.Label(header,text="v10.0",font=("微软雅黑",10),bg=self.colors['bg_light'],fg=self.colors['text_gray']).pack(side='left',padx=10)
        self.time_label=tk.Label(header,text="",font=("微软雅黑",10),bg=self.colors['bg_light'],fg=self.colors['text_gray'])
        self.time_label.pack(side='right',padx=15)
        self.update_time()
        self.sound_var=tk.BooleanVar(value=self.sound_enabled)
        tk.Checkbutton(header,text="🔊 音效",variable=self.sound_var,command=self.toggle_sound,bg=self.colors['bg_light'],fg='white',selectcolor=self.colors['bg_light']).pack(side='right',padx=10)
        
        main_paned=tk.PanedWindow(self.root,bg=self.colors['bg_dark'],sashwidth=5)
        main_paned.pack(fill='both',expand=True)
        left_panel=tk.Frame(main_paned,bg=self.colors['bg_medium'],width=450)
        main_paned.add(left_panel,width=450)
        left_panel.pack_propagate(False)
        
        canvas=tk.Canvas(left_panel,bg=self.colors['bg_medium'],highlightthickness=0)
        scrollbar=tk.Scrollbar(left_panel,orient="vertical",command=canvas.yview)
        scrollable=tk.Frame(canvas,bg=self.colors['bg_medium'])
        scrollable.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=scrollable,anchor="nw",width=430)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left",fill="both",expand=True)
        scrollbar.pack(side="right",fill="y")
        canvas.bind_all("<MouseWheel>",lambda e:canvas.yview_scroll(int(-1*(e.delta/120)),"units"))
        
        tk.Label(scrollable,text="🎮 服务器控制中心",font=("微软雅黑",18,"bold"),bg=self.colors['bg_medium'],fg='white').pack(pady=15)
        self.setup_status_card(scrollable)
        self.setup_cheat_card(scrollable)  # 新增：作弊模式开关
        self.setup_gamerules_card(scrollable)
        self.setup_server_settings_card(scrollable)
        self.setup_multiplayer_card(scrollable)
        self.setup_backup_card(scrollable)
        
        right_panel=tk.Frame(main_paned,bg=self.colors['bg_dark'])
        main_paned.add(right_panel,width=1150)
        notebook=ttk.Notebook(right_panel)
        notebook.pack(fill='both',expand=True,padx=5,pady=5)
        self.setup_console_tab(notebook)
        self.setup_players_tab(notebook)
        self.setup_backup_tab(notebook)
        self.setup_invite_tab(notebook)
        self.setup_help_tab(notebook)
    
    def update_time(self):
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000,self.update_time)
    
    def toggle_sound(self):
        self.sound_enabled=self.sound_var.get()
        self.save_all_configs()
        if self.sound_enabled: self.play_sound('startup')
    
    def setup_cheat_card(self,p):
        """作弊模式控制卡片"""
        card=tk.LabelFrame(p,text="⚠️ 作弊/管理员模式",font=("微软雅黑",11,"bold"),bg=self.colors['bg_medium'],fg='white',bd=2,relief='ridge')
        card.pack(fill='x',padx=10,pady=10)
        
        # 主开关
        main_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        main_frame.pack(fill='x',pady=5,padx=10)
        
        self.cheats_var=tk.BooleanVar(value=self.allow_cheats)
        self.cheats_switch=tk.Checkbutton(main_frame,text="🔓 开启作弊模式 (允许使用/gamemode, /give等命令)",variable=self.cheats_var,command=self.toggle_cheats,font=("微软雅黑",10),bg=self.colors['bg_medium'],fg=self.colors['accent_yellow'],selectcolor=self.colors['bg_medium'])
        self.cheats_switch.pack(side='left')
        
        self.cheats_status=tk.Label(main_frame,text="✅ 已开启" if self.allow_cheats else "❌ 已关闭",font=("微软雅牙",9),bg=self.colors['bg_medium'],fg=self.colors['accent_green'] if self.allow_cheats else self.colors['accent_red'])
        self.cheats_status.pack(side='right')
        
        # 快速作弊命令按钮
        btn_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        btn_frame.pack(fill='x',pady=5,padx=10)
        
        tk.Label(btn_frame,text="📦 快速作弊命令:",font=("微软雅黑",9),bg=self.colors['bg_medium'],fg=self.colors['text_gray']).pack(anchor='w')
        
        cheat_btns_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        cheat_btns_frame.pack(fill='x',pady=5,padx=10)
        
        cheat_commands=[
            ("🎮 切换创造模式", "gamemode creative @a"),
            ("⚔️ 切换生存模式", "gamemode survival @a"),
            ("💎 给予钻石", "give @a diamond 64"),
            ("❤️ 满血恢复", "effect @a instant_health 1 10"),
            ("✨ 经验值", "xp 1000 @a"),
            ("🌙 设置时间白天", "time set day"),
            ("🌃 设置时间夜晚", "time set night"),
            ("🔨 获得命令方块", "give @a command_block 10"),
            ("🛡️ 无敌效果", "effect @a resistance 60 5"),
            ("🏃 速度提升", "effect @a speed 60 3"),
            ("🪦 杀死所有怪物", "kill @e[type=zombie,type=skeleton,type=creeper]"),
            ("🧹 清除掉落物", "kill @e[type=item]")
        ]
        
        for i,(text,cmd) in enumerate(cheat_commands):
            btn=tk.Button(cheat_btns_frame,text=text,command=lambda c=cmd: self.send_cheat_command(c),font=("微软雅黑",8),bg=self.colors['accent_purple'],fg='white',relief='flat',width=14)
            btn.grid(row=i//3,column=i%3,padx=2,pady=2,sticky='ew')
            btn.bind("<Enter>",lambda e,b=btn: b.config(bg=self.colors['accent_blue']))
            btn.bind("<Leave>",lambda e,b=btn: b.config(bg=self.colors['accent_purple']))
        
        # 针对特定玩家作弊
        player_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        player_frame.pack(fill='x',pady=5,padx=10)
        
        tk.Label(player_frame,text="👤 针对特定玩家:",font=("微软雅黑",9),bg=self.colors['bg_medium'],fg=self.colors['text_gray']).pack(anchor='w')
        
        player_cheat_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        player_cheat_frame.pack(fill='x',pady=5,padx=10)
        
        self.cheat_target_var=tk.StringVar()
        self.cheat_target_entry=tk.Entry(player_cheat_frame,textvariable=self.cheat_target_var,width=15,bg=self.colors['console_bg'],fg='white',font=("微软雅黑",9))
        self.cheat_target_entry.pack(side='left',padx=5)
        self.cheat_target_entry.insert(0,"玩家名")
        self.cheat_target_entry.bind("<FocusIn>",lambda e: self.cheat_target_entry.delete(0,tk.END) if self.cheat_target_entry.get()=="玩家名" else None)
        
        tk.Button(player_cheat_frame,text="给钻石",command=lambda: self.send_cheat_command(f"give {self.get_cheat_target()} diamond 64"),bg=self.colors['accent_green'],fg='white',relief='flat',width=8).pack(side='left',padx=2)
        tk.Button(player_cheat_frame,text="创造模式",command=lambda: self.send_cheat_command(f"gamemode creative {self.get_cheat_target()}"),bg=self.colors['accent_blue'],fg='white',relief='flat',width=10).pack(side='left',padx=2)
        tk.Button(player_cheat_frame,text="生存模式",command=lambda: self.send_cheat_command(f"gamemode survival {self.get_cheat_target()}"),bg=self.colors['accent_orange'],fg='white',relief='flat',width=10).pack(side='left',padx=2)
        tk.Button(player_cheat_frame,text="满血",command=lambda: self.send_cheat_command(f"effect {self.get_cheat_target()} instant_health 1 10"),bg=self.colors['accent_green'],fg='white',relief='flat',width=6).pack(side='left',padx=2)
        
        # 提示信息
        tip_label=tk.Label(card,text="💡 提示：需要先开启作弊模式才能使用这些命令",font=("微软雅黑",8),bg=self.colors['bg_medium'],fg=self.colors['text_gray'])
        tip_label.pack(pady=5)
    
    def get_cheat_target(self):
        target=self.cheat_target_var.get().strip()
        if not target or target=="玩家名":
            return "@a"
        return target
    
    def toggle_cheats(self):
        self.allow_cheats=self.cheats_var.get()
        self.save_all_configs()
        self.cheats_status.config(text="✅ 已开启" if self.allow_cheats else "❌ 已关闭",fg=self.colors['accent_green'] if self.allow_cheats else self.colors['accent_red'])
        if self.server_running:
            self.send_command(f"gamerule sendcommandfeedback true")
            if self.allow_cheats:
                self.send_command("gamerule commandblockoutput true")
                self.log_to_console("🔓 作弊模式已开启，OP玩家可以使用作弊命令")
            else:
                self.log_to_console("🔒 作弊模式已关闭")
        self.log_to_console(f"⚠️ 作弊模式: {'开启' if self.allow_cheats else '关闭'}")
    
    def send_cheat_command(self,cmd):
        if not self.allow_cheats:
            messagebox.showwarning("作弊模式未开启","请先开启作弊模式！\n在左侧【作弊/管理员模式】中开启开关")
            return
        if not self.server_running:
            messagebox.showwarning("服务器未运行","请先启动服务器")
            return
        self.send_command(cmd)
        self.log_to_console(f"✨ 执行作弊命令: {cmd}")
    
    def setup_status_card(self,p):
        card=tk.Frame(p,bg=self.colors['bg_light'],relief='ridge',bd=2)
        card.pack(fill='x',padx=10,pady=10)
        self.status_label=tk.Label(card,text="● 服务器离线",font=("微软雅黑",14,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_red'])
        self.status_label.pack(pady=10)
        self.uptime_label=tk.Label(card,text="运行时间: --:--:--",font=("微软雅黑",10),bg=self.colors['bg_light'],fg='gray')
        self.uptime_label.pack()
        btn_frame=tk.Frame(card,bg=self.colors['bg_light'])
        btn_frame.pack(pady=10)
        self.start_btn=tk.Button(btn_frame,text="▶ 启动",command=self.start_server,font=("微软雅黑",11),bg=self.colors['accent_green'],fg='white',width=8,relief='flat')
        self.start_btn.pack(side='left',padx=3)
        self.stop_btn=tk.Button(btn_frame,text="■ 停止",command=self.stop_server,font=("微软雅黑",11),bg=self.colors['accent_red'],fg='white',width=8,relief='flat',state='disabled')
        self.stop_btn.pack(side='left',padx=3)
        self.force_stop_btn=tk.Button(btn_frame,text="⚠ 强制关闭",command=self.force_stop_server,font=("微软雅黑",10),bg=self.colors['accent_orange'],fg='white',width=10,relief='flat',state='disabled')
        self.force_stop_btn.pack(side='left',padx=3)
        self.restart_btn=tk.Button(btn_frame,text="⟳ 重启",command=self.restart_server,font=("微软雅黑",11),bg=self.colors['accent_yellow'],fg='white',width=8,relief='flat',state='disabled')
        self.restart_btn.pack(side='left',padx=3)
        path_frame=tk.Frame(p,bg=self.colors['bg_medium'])
        path_frame.pack(fill='x',padx=10,pady=5)
        tk.Label(path_frame,text="📁 服务器文件",font=("微软雅黑",9),bg=self.colors['bg_medium'],fg='gray').pack(anchor='w')
        self.path_value=tk.Label(path_frame,text=os.path.basename(self.server_exe) if os.path.exists(self.server_exe) else "未找到",font=("微软雅黑",9),bg=self.colors['bg_medium'],fg=self.colors['accent_green'])
        self.path_value.pack(anchor='w')
        tk.Button(path_frame,text="选择文件",command=self.select_server,font=("微软雅黑",9),bg=self.colors['accent_blue'],fg='white',relief='flat').pack(anchor='w',pady=5)
    
    def setup_server_settings_card(self,p):
        card=tk.LabelFrame(p,text="⚙️ 服务器基本设置",font=("微软雅黑",11,"bold"),bg=self.colors['bg_medium'],fg='white',bd=2,relief='ridge')
        card.pack(fill='x',padx=10,pady=10)
        f=tk.Frame(card,bg=self.colors['bg_medium'])
        f.pack(fill='x',pady=5,padx=10)
        tk.Label(f,text="👥 最大玩家数:",font=("微软雅黑",10),bg=self.colors['bg_medium'],fg='white').pack(side='left')
        self.max_players_var=tk.StringVar(value=self.server_settings.get("max-players","20"))
        tk.Spinbox(f,from_=1,to=100,textvariable=self.max_players_var,width=8,font=("微软雅黑",10)).pack(side='left',padx=5)
        tk.Button(f,text="应用",command=self.apply_max_players,font=("微软雅黑",9),bg=self.colors['accent_blue'],fg='white',relief='flat').pack(side='left',padx=5)
        f=tk.Frame(card,bg=self.colors['bg_medium'])
        f.pack(fill='x',pady=5,padx=10)
        tk.Label(f,text="🎮 默认游戏模式:",font=("微软雅黑",10),bg=self.colors['bg_medium'],fg='white').pack(side='left')
        self.gamemode_var=tk.StringVar(value=self.server_settings.get("gamemode","survival"))
        ttk.Combobox(f,textvariable=self.gamemode_var,values=["survival","creative","adventure","spectator"],width=12,state="readonly").pack(side='left',padx=5)
        tk.Button(f,text="应用",command=self.apply_gamemode,font=("微软雅黑",9),bg=self.colors['accent_blue'],fg='white',relief='flat').pack(side='left',padx=5)
        f=tk.Frame(card,bg=self.colors['bg_medium'])
        f.pack(fill='x',pady=5,padx=10)
        tk.Label(f,text="⚔️ 难度:",font=("微软雅黑",10),bg=self.colors['bg_medium'],fg='white').pack(side='left')
        self.difficulty_var=tk.StringVar(value=self.server_settings.get("difficulty","normal"))
        ttk.Combobox(f,textvariable=self.difficulty_var,values=["peaceful","easy","normal","hard"],width=12,state="readonly").pack(side='left',padx=5)
        tk.Button(f,text="应用",command=self.apply_difficulty,font=("微软雅黑",9),bg=self.colors['accent_blue'],fg='white',relief='flat').pack(side='left',padx=5)
        f=tk.Frame(card,bg=self.colors['bg_medium'])
        f.pack(fill='x',pady=5,padx=10)
        self.online_mode_var=tk.BooleanVar(value=self.online_mode)
        tk.Checkbutton(f,text="✅ 正版验证",variable=self.online_mode_var,command=self.save_online_mode,bg=self.colors['bg_medium'],fg='white',selectcolor=self.colors['bg_medium']).pack(side='left',padx=5)
        self.command_blocks_var=tk.BooleanVar(value=self.command_blocks)
        tk.Checkbutton(f,text="🔧 命令方块",variable=self.command_blocks_var,command=self.save_command_blocks,bg=self.colors['bg_medium'],fg='white',selectcolor=self.colors['bg_medium']).pack(side='left',padx=20)
        tk.Button(f,text="💾 保存所有设置",command=self.save_all_server_settings,font=("微软雅黑",9),bg=self.colors['accent_green'],fg='white',relief='flat').pack(side='right',padx=5)
    
    def apply_max_players(self):
        try:
            mp=int(self.max_players_var.get())
            self.server_settings["max-players"]=str(mp)
            self.save_all_configs()
            self.send_command(f"setmaxplayers {mp}")
            self.log_to_console(f"👥 最大玩家数: {mp}")
        except: pass
    def apply_gamemode(self): self.send_command(f"defaultgamemode {self.gamemode_var.get()}")
    def apply_difficulty(self): self.send_command(f"difficulty {self.difficulty_var.get()}")
    def save_online_mode(self): self.online_mode=self.online_mode_var.get();self.save_all_configs()
    def save_command_blocks(self): self.command_blocks=self.command_blocks_var.get();self.save_all_configs()
    def save_all_server_settings(self): self.save_all_configs();self.update_server_properties()
    
    def setup_gamerules_card(self,p):
        card=tk.LabelFrame(p,text="🎮 游戏规则控制",font=("微软雅黑",11,"bold"),bg=self.colors['bg_medium'],fg='white',bd=2,relief='ridge')
        card.pack(fill='x',padx=10,pady=10)
        lf,rf=tk.Frame(card,bg=self.colors['bg_medium']),tk.Frame(card,bg=self.colors['bg_medium'])
        lf.pack(side='left',fill='both',expand=True,padx=5,pady=5)
        rf.pack(side='right',fill='both',expand=True,padx=5,pady=5)
        rules=[("💎 保留物品","keepInventory",False),("🔥 火焰蔓延","doFireTick",True),("💣 TNT爆炸","tntExplodes",True),("⚔️ PVP","pvp",True),("🔄 立即重生","doImmediateRespawn",False),("❤️ 自然恢复","naturalRegeneration",True),("💬 死亡消息","showDeathMessages",True),("👹 生物生成","doMobSpawning",True),("🌤️ 天气循环","doWeatherCycle",True),("☀️ 昼夜循环","doDaylightCycle",True),("🔧 命令方块输出","commandBlockOutput",True),("🐷 生物破坏","mobGriefing",True),("📦 实体掉落","doEntityDrops",True),("🧱 方块掉落","doTileDrops",True),("📢 成就广播","announceAdvancements",True)]
        self.gamerule_vars,self.gamerule_buttons={},{}
        for i,(d,r,_) in enumerate(rules):
            t=lf if i<len(rules)//2 else rf
            f=tk.Frame(t,bg=self.colors['bg_medium'])
            f.pack(fill='x',pady=3,padx=5)
            v=self.gamerules.get(r,False)
            self.gamerule_vars[r]=tk.BooleanVar(value=v)
            btn=tk.Button(f,text=d,command=lambda rn=r:self.toggle_gamerule(rn),font=("微软雅黑",9),width=16,anchor='w',bg=self.colors['accent_green'] if v else self.colors['accent_red'],fg='white',relief='flat')
            btn.pack(side='left')
            lbl=tk.Label(f,text="✅ 开启" if v else "❌ 关闭",font=("微软雅黑",8),bg=self.colors['bg_medium'],fg=self.colors['accent_green'] if v else self.colors['accent_red'])
            lbl.pack(side='left',padx=10)
            self.gamerule_buttons[r]=(btn,lbl)
        bf=tk.Frame(card,bg=self.colors['bg_medium'])
        bf.pack(fill='x',pady=10,padx=10)
        tk.Label(bf,text="⚡ 批量操作:",font=("微软雅黑",9,"bold"),bg=self.colors['bg_medium'],fg='white').pack(side='left',padx=5)
        tk.Button(bf,text="全部开启",command=self.all_gamerules_on,bg=self.colors['accent_green'],fg='white',relief='flat',width=10).pack(side='left',padx=5)
        tk.Button(bf,text="全部关闭",command=self.all_gamerules_off,bg=self.colors['accent_red'],fg='white',relief='flat',width=10).pack(side='left',padx=5)
        tk.Button(bf,text="🏕️ 生存推荐",command=self.set_survival_rules,bg=self.colors['accent_blue'],fg='white',relief='flat',width=10).pack(side='left',padx=5)
        tk.Button(bf,text="🎨 创造推荐",command=self.set_creative_rules,bg=self.colors['accent_purple'],fg='white',relief='flat',width=10).pack(side='left',padx=5)
    
    def toggle_gamerule(self,rn):
        v=not self.gamerule_vars[rn].get()
        self.gamerule_vars[rn].set(v)
        self.gamerules[rn]=v
        btn,lbl=self.gamerule_buttons[rn]
        btn.config(bg=self.colors['accent_green'] if v else self.colors['accent_red'])
        lbl.config(text="✅ 开启" if v else "❌ 关闭",fg=self.colors['accent_green'] if v else self.colors['accent_red'])
        self.send_command(f"gamerule {rn} {'true' if v else 'false'}")
        self.save_all_configs()
    def all_gamerules_on(self): [self.toggle_gamerule(r) for r in self.gamerule_vars if not self.gamerule_vars[r].get()]
    def all_gamerules_off(self): [self.toggle_gamerule(r) for r in self.gamerule_vars if self.gamerule_vars[r].get()]
    def set_survival_rules(self):
        for r,v in [("keepInventory",False),("doFireTick",True),("tntExplodes",True),("pvp",True),("doImmediateRespawn",False),("naturalRegeneration",True),("showDeathMessages",True),("doMobSpawning",True),("doWeatherCycle",True),("doDaylightCycle",True),("mobGriefing",True),("doEntityDrops",True),("doTileDrops",True)]:
            if r in self.gamerule_vars and self.gamerule_vars[r].get()!=v: self.toggle_gamerule(r)
    def set_creative_rules(self):
        for r,v in [("keepInventory",True),("doFireTick",False),("tntExplodes",False),("pvp",False),("doImmediateRespawn",True),("doMobSpawning",False),("doWeatherCycle",False),("mobGriefing",False)]:
            if r in self.gamerule_vars and self.gamerule_vars[r].get()!=v: self.toggle_gamerule(r)
    
    def setup_multiplayer_card(self,p):
        card=tk.LabelFrame(p,text="🌐 好友联机设置",font=("微软雅黑",11,"bold"),bg=self.colors['bg_medium'],fg='white',bd=2,relief='ridge')
        card.pack(fill='x',padx=10,pady=10)
        tk.Label(card,text="📌 通过微软/Xbox好友系统联机",font=("微软雅黑",9),bg=self.colors['bg_medium'],fg=self.colors['accent_green']).pack(anchor='w',pady=5,padx=10)
        self.friend_permission=tk.StringVar(value="friends_of_friends")
        for t,v in [("🔒 仅邀请","invite_only"),("👥 仅好友","friends_only"),("🌟 好友的好友","friends_of_friends")]:
            tk.Radiobutton(card,text=t,variable=self.friend_permission,value=v,bg=self.colors['bg_medium'],fg='white',selectcolor=self.colors['bg_medium']).pack(anchor='w',padx=20)
        self.lan_visible=tk.BooleanVar(value=True)
        tk.Checkbutton(card,text="📡 对局域网玩家可见",variable=self.lan_visible,bg=self.colors['bg_medium'],fg='white',selectcolor=self.colors['bg_medium']).pack(anchor='w',pady=5,padx=10)
        tk.Button(card,text="💾 保存联机设置",command=self.save_multiplayer_settings,bg=self.colors['accent_green'],fg='white',relief='flat').pack(pady=10,padx=10,fill='x')
        
        # IP地址显示区域（增强版）
        ipf=tk.Frame(card,bg=self.colors['bg_light'],relief='ridge',bd=1)
        ipf.pack(fill='x',pady=5,padx=10)
        tk.Label(ipf,text="🖥️ 本机IP:",bg=self.colors['bg_light'],fg='gray').grid(row=0,column=0,padx=5,pady=2,sticky='w')
        self.local_ip_label=tk.Label(ipf,text=self.local_ip,font=("微软雅黑",9,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_green'])
        self.local_ip_label.grid(row=0,column=1,padx=5,pady=2)
        tk.Button(ipf,text="复制",command=self.copy_local_ip,bg=self.colors['accent_blue'],fg='white',relief='flat',width=6).grid(row=0,column=2,padx=5,pady=2)
        
        # 外网IP（供外网好友连接）
        tk.Label(ipf,text="🌐 外网IP:",bg=self.colors['bg_light'],fg='gray').grid(row=1,column=0,padx=5,pady=2,sticky='w')
        self.public_ip_label=tk.Label(ipf,text=self.public_ip if self.public_ip else "获取失败",font=("微软雅黑",9,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_yellow'])
        self.public_ip_label.grid(row=1,column=1,padx=5,pady=2)
        tk.Button(ipf,text="复制",command=self.copy_public_ip,bg=self.colors['accent_blue'],fg='white',relief='flat',width=6).grid(row=1,column=2,padx=5,pady=2)
        
        # 刷新IP按钮
        refresh_ip_btn=tk.Button(ipf,text="🔄 刷新外网IP",command=self.refresh_public_ip,bg=self.colors['accent_purple'],fg='white',relief='flat',width=12)
        refresh_ip_btn.grid(row=2,column=0,columnspan=3,pady=5)
        
        # 内网穿透提示
        tip_frame=tk.Frame(card,bg=self.colors['bg_medium'])
        tip_frame.pack(fill='x',pady=5,padx=10)
        tk.Label(tip_frame,text="💡 外网IP说明：",font=("微软雅黑",9,"bold"),bg=self.colors['bg_medium'],fg=self.colors['accent_yellow']).pack(anchor='w')
        tk.Label(tip_frame,text="• 使用外网IP需要路由器设置端口映射(端口19132)\n• 或者使用内网穿透工具(如SakuraFrp、Ngrok)\n• 好友需要填写服务器地址：IP地址:端口号",font=("微软雅黑",8),bg=self.colors['bg_medium'],fg=self.colors['text_gray'],justify='left').pack(anchor='w')
    
    def copy_local_ip(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.local_ip)
        self.log_to_console(f"📋 本机IP已复制: {self.local_ip}")
        messagebox.showinfo("复制成功",f"本机IP已复制：{self.local_ip}")
    
    def copy_public_ip(self):
        if self.public_ip:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.public_ip)
            self.log_to_console(f"📋 外网IP已复制: {self.public_ip}")
            messagebox.showinfo("复制成功",f"外网IP已复制：{self.public_ip}\n\n⚠️ 注意：\n1. 需要设置路由器端口映射(19132)\n2. 或使用内网穿透工具")
        else:
            messagebox.showwarning("IP获取失败","请点击【刷新外网IP】重新获取")
    
    def refresh_public_ip(self):
        self.public_ip=self.get_public_ip()
        if self.public_ip:
            self.public_ip_label.config(text=self.public_ip,fg=self.colors['accent_yellow'])
            self.log_to_console(f"🌐 外网IP已刷新: {self.public_ip}")
            messagebox.showinfo("刷新成功",f"外网IP: {self.public_ip}")
        else:
            self.public_ip_label.config(text="获取失败",fg=self.colors['accent_red'])
            self.log_to_console("❌ 外网IP获取失败")
            messagebox.showerror("获取失败","无法获取外网IP，请检查网络连接")
    
    def save_multiplayer_settings(self):
        p=self.friend_permission.get()
        self.multiplayer_settings["allow_friends"]=True
        self.multiplayer_settings["allow_friends_of_friends"]=(p=="friends_of_friends")
        self.multiplayer_settings["visible_to_lan"]=self.lan_visible.get()
        self.save_all_configs()
        self.update_server_properties()
        self.play_sound('backup')
    
    def update_server_properties(self):
        prop=os.path.join(os.path.dirname(self.server_exe),"server.properties")
        if os.path.exists(prop):
            try:
                with open(prop,'r',encoding='utf-8') as f: lines=f.readlines()
                for i,l in enumerate(lines):
                    if l.startswith("online-mode="): lines[i]=f"online-mode={'on' if self.online_mode else 'off'}\n"
                    elif l.startswith("enable-command-block="): lines[i]=f"enable-command-block={'on' if self.command_blocks else 'off'}\n"
                    elif l.startswith("max-players="): lines[i]=f"max-players={self.server_settings.get('max-players','20')}\n"
                with open(prop,'w',encoding='utf-8') as f: f.writelines(lines)
            except: pass
    
    def setup_backup_card(self,p):
        card=tk.LabelFrame(p,text="💾 自动备份设置",font=("微软雅黑",11,"bold"),bg=self.colors['bg_medium'],fg='white',bd=2,relief='ridge')
        card.pack(fill='x',padx=10,pady=10)
        tf=tk.Frame(card,bg=self.colors['bg_medium'])
        tf.pack(fill='x',pady=5,padx=10)
        self.backup_enabled_var=tk.BooleanVar(value=self.auto_backup_enabled)
        self.backup_switch=tk.Checkbutton(tf,text="启用自动备份",variable=self.backup_enabled_var,command=self.toggle_auto_backup,bg=self.colors['bg_medium'],fg='white',selectcolor=self.colors['bg_medium'])
        self.backup_switch.pack(side='left')
        self.backup_status=tk.Label(tf,text="● 运行中" if self.auto_backup_enabled else "● 已停止",bg=self.colors['bg_medium'],fg=self.colors['accent_green'] if self.auto_backup_enabled else self.colors['accent_red'])
        self.backup_status.pack(side='right')
        iframe=tk.Frame(card,bg=self.colors['bg_medium'])
        iframe.pack(fill='x',pady=5,padx=10)
        tk.Label(iframe,text="备份间隔:",bg=self.colors['bg_medium'],fg='white').pack(side='left')
        self.interval_var=tk.StringVar(value=str(self.backup_interval))
        tk.Spinbox(iframe,from_=5,to=360,textvariable=self.interval_var,width=8,font=("微软雅黑",10)).pack(side='left',padx=5)
        tk.Label(iframe,text="分钟",bg=self.colors['bg_medium'],fg='white').pack(side='left')
        kf=tk.Frame(card,bg=self.colors['bg_medium'])
        kf.pack(fill='x',pady=5,padx=10)
        tk.Label(kf,text="保留备份数:",bg=self.colors['bg_medium'],fg='white').pack(side='left')
        self.keep_var=tk.StringVar(value=str(self.keep_backups))
        tk.Spinbox(kf,from_=1,to=100,textvariable=self.keep_var,width=8,font=("微软雅黑",10)).pack(side='left',padx=5)
        tk.Button(card,text="📀 立即手动备份",command=self.manual_backup,bg=self.colors['accent_green'],fg='white',relief='flat').pack(pady=10,padx=10,fill='x')
        self.last_backup_label=tk.Label(card,text="最后备份: 无",bg=self.colors['bg_medium'],fg='gray')
        self.last_backup_label.pack(pady=5)
        if self.auto_backup_enabled: self.start_auto_backup()
    
    def toggle_auto_backup(self):
        self.auto_backup_enabled=self.backup_enabled_var.get()
        self.save_all_configs()
        self.backup_status.config(text="● 运行中" if self.auto_backup_enabled else "● 已停止",fg=self.colors['accent_green'] if self.auto_backup_enabled else self.colors['accent_red'])
        if self.auto_backup_enabled: self.start_auto_backup()
    def start_auto_backup(self):
        def loop():
            while self.auto_backup_enabled:
                time.sleep(self.backup_interval*60)
                if self.auto_backup_enabled: self.perform_backup(True)
        threading.Thread(target=loop,daemon=True).start()
    def manual_backup(self): self.perform_backup(False)
    
    def perform_backup(self,automatic):
        try:
            if self.server_running:
                self.send_command("save-all")
                time.sleep(2)
                self.send_command("save-off")
                time.sleep(1)
            ts=datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name=f"backup_{ts}"
            backup_path=os.path.join(self.backup_folder,backup_name)
            if os.path.exists(self.worlds_folder) and os.listdir(self.worlds_folder):
                shutil.copytree(self.worlds_folder,backup_path)
                size_mb=self.get_folder_size(backup_path)/(1024*1024)
                self.log_to_console(f"✅ 备份完成: {backup_name} ({size_mb:.2f}MB)")
                self.last_backup_label.config(text=f"最后备份: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.cleanup_old_backups()
                self.refresh_backup_list()
                self.play_sound('backup')
                messagebox.showinfo("备份完成",f"✅ 备份成功！\n📁 {backup_name}\n📊 大小: {size_mb:.2f}MB\n👑 制作：houukhhk")
            if self.server_running: self.send_command("save-on")
        except Exception as e: self.log_to_console(f"❌ 备份失败: {e}")
    
    def cleanup_old_backups(self):
        try:
            backups=[d for d in os.listdir(self.backup_folder) if os.path.isdir(os.path.join(self.backup_folder,d)) and d.startswith("backup_")]
            backups.sort(reverse=True)
            for old in backups[self.keep_backups:]:
                shutil.rmtree(os.path.join(self.backup_folder,old))
        except: pass
    
    def refresh_backup_list(self):
        for i in self.backup_tree.get_children(): self.backup_tree.delete(i)
        try:
            backups=[d for d in os.listdir(self.backup_folder) if os.path.isdir(os.path.join(self.backup_folder,d)) and d.startswith("backup_")]
            for b in sorted(backups,reverse=True):
                size_mb=self.get_folder_size(os.path.join(self.backup_folder,b))/(1024*1024)
                self.backup_tree.insert("","end",values=(b,f"{size_mb:.2f}",b.replace("backup_","")[:15]))
        except: pass
    
    def get_folder_size(self,folder):
        total=0
        for dp,dn,fn in os.walk(folder):
            for f in fn:
                try: total+=os.path.getsize(os.path.join(dp,f))
                except: pass
        return total
    
    def select_server(self):
        f=filedialog.askopenfilename(title="选择 bedrock_server.exe",filetypes=[("可执行文件","*.exe")])
        if f: self.server_exe=f;self.path_value.config(text=os.path.basename(f));self.save_all_configs()
    
    def start_server(self):
        if not os.path.exists(self.server_exe): messagebox.showerror("错误","找不到服务器文件");return
        try:
            os.chdir(os.path.dirname(self.server_exe))
            self.server_process=subprocess.Popen([self.server_exe],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE,text=True,bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
            self.server_running=True
            self.start_time=time.time()
            self.update_ui_state()
            self.log_to_console("✅ 服务器启动成功！")
            threading.Thread(target=self.read_output,daemon=True).start()
            threading.Thread(target=self.update_uptime,daemon=True).start()
        except Exception as e: messagebox.showerror("启动失败",str(e))
    
    def read_output(self):
        while self.server_running and self.server_process:
            try:
                line=self.server_process.stdout.readline()
                if line:
                    self.log_to_console(line.strip())
                    if "joined the game" in line.lower():
                        self.play_sound('player_join')
                        self.refresh_players()
                    elif "left the game" in line.lower():
                        self.play_sound('player_leave')
                        self.refresh_players()
                else: break
            except: break
        if self.server_running: self.server_running=False;self.update_ui_state()
    
    def update_uptime(self):
        while self.server_running:
            e=int(time.time()-self.start_time)
            self.root.after(0,lambda: self.uptime_label.config(text=f"运行时间: {e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}"))
            time.sleep(1)
    
    def stop_server(self):
        if self.server_process and self.server_running:
            self.send_command("stop")
            def wait():
                for _ in range(30):
                    time.sleep(1)
                    if self.server_process.poll() is not None:
                        self.server_running=False
                        self.update_ui_state()
                        return
            threading.Thread(target=wait,daemon=True).start()
    
    def force_stop_server(self):
        if self.server_process:
            os.system(f"taskkill /F /PID {self.server_process.pid} 2>nul")
            self.server_running=False
            self.update_ui_state()
    
    def restart_server(self):
        if self.server_running: self.stop_server();time.sleep(3)
        self.start_server()
    
    def send_command(self,cmd=None):
        if cmd is None: cmd=self.cmd_entry.get().strip()
        if not cmd: return
        if not self.server_running: self.log_to_console("❌ 服务器未运行");return
        try:
            self.server_process.stdin.write(cmd+"\n")
            self.server_process.stdin.flush()
            self.log_to_console(f">>> {cmd}")
            if hasattr(self,'cmd_entry'): self.cmd_entry.delete(0,tk.END)
        except Exception as e: self.log_to_console(f"❌ 发送失败: {e}")
    
    def quick_command(self,cmd): self.send_command(cmd)
    
    def start_player_refresh(self):
        def refresh_loop():
            while True:
                time.sleep(5)
                if self.server_running: self.refresh_players()
        threading.Thread(target=refresh_loop,daemon=True).start()
    
    def refresh_players(self):
        if not self.server_running: return
        self.online_players=[]
        self.root.after(0,lambda: self.online_listbox.delete(0,tk.END))
        self.send_command("list")
    
    def kick_player(self):
        s=self.online_listbox.curselection()
        if s:
            p=self.online_listbox.get(s[0]).split(" - ")[0] if " - " in self.online_listbox.get(s[0]) else self.online_listbox.get(s[0])
            r=simpledialog.askstring("踢出玩家",f"踢出 {p} 的原因:")
            if r: self.send_command(f"kick {p} {r}")
    
    def ban_player(self):
        s=self.online_listbox.curselection()
        if s:
            p=self.online_listbox.get(s[0]).split(" - ")[0] if " - " in self.online_listbox.get(s[0]) else self.online_listbox.get(s[0])
            r=simpledialog.askstring("封禁玩家",f"封禁 {p} 的原因:")
            if r: self.send_command(f"ban {p} {r}")
    
    def unban_player(self):
        s=self.ban_listbox.curselection()
        if s:
            p=self.ban_listbox.get(s[0]).split(" - ")[0]
            self.send_command(f"pardon {p}")
    
    def set_op(self):
        s=self.online_listbox.curselection()
        if s:
            p=self.online_listbox.get(s[0]).split(" - ")[0] if " - " in self.online_listbox.get(s[0]) else self.online_listbox.get(s[0])
            self.send_command(f"op {p}")
    
    def log_to_console(self,msg):
        def _log(): self.console.insert(tk.END,f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n");self.console.see(tk.END)
        self.root.after(0,_log)
    
    def clear_console(self): self.console.delete(1.0,tk.END)
    
    def update_ui_state(self):
        def _update():
            if self.server_running:
                self.status_label.config(text="● 服务器运行中",fg=self.colors['accent_green'])
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
                self.force_stop_btn.config(state='normal')
                self.restart_btn.config(state='normal')
            else:
                self.status_label.config(text="● 服务器离线",fg=self.colors['accent_red'])
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
                self.force_stop_btn.config(state='disabled')
                self.restart_btn.config(state='disabled')
                self.uptime_label.config(text="运行时间: --:--:--")
        self.root.after(0,_update)
    
    def restore_backup(self):
        s=self.backup_tree.selection()
        if not s: messagebox.showwarning("警告","请先选择一个备份");return
        bn=self.backup_tree.item(s[0])['values'][0]
        if messagebox.askyesno("确认回档",f"确定要回档到 {bn} 吗？"):
            try:
                wr=self.server_running
                if wr: self.stop_server();time.sleep(3)
                pre=f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if os.path.exists(self.worlds_folder) and os.listdir(self.worlds_folder):
                    shutil.copytree(self.worlds_folder,os.path.join(self.backup_folder,pre))
                shutil.rmtree(self.worlds_folder)
                shutil.copytree(os.path.join(self.backup_folder,bn),self.worlds_folder)
                self.log_to_console(f"✅ 回档成功: {bn}")
                if wr: self.start_server()
                messagebox.showinfo("成功","回档完成！")
            except Exception as e: messagebox.showerror("失败",str(e))
    
    def delete_backup(self):
        s=self.backup_tree.selection()
        if s and messagebox.askyesno("确认",f"删除 {self.backup_tree.item(s[0])['values'][0]}?"):
            shutil.rmtree(os.path.join(self.backup_folder,self.backup_tree.item(s[0])['values'][0]))
            self.refresh_backup_list()
    
    def generate_invite_code(self):
        import random,string
        code=''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
        self.invite_code_label.config(text=code)
        self.invite_link.delete(0,tk.END)
        self.invite_link.insert(0,f"minecraft://acceptRealmInvite?inviteCode={code}")
    
    def copy_invite_link(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.invite_link.get())
        messagebox.showinfo("成功","邀请链接已复制！")
    
    def setup_console_tab(self,nb):
        t=tk.Frame(nb,bg=self.colors['bg_light'])
        nb.add(t,text="💻 控制台")
        cf=tk.Frame(t,bg=self.colors['bg_light'])
        cf.pack(fill='both',expand=True,padx=10,pady=10)
        tf=tk.Frame(cf,bg=self.colors['bg_medium'])
        tf.pack(fill='x')
        tk.Label(tf,text="📟 实时控制台",font=("微软雅黑",10,"bold"),bg=self.colors['bg_medium'],fg=self.colors['accent_green']).pack(side='left',padx=10,pady=5)
        tk.Button(tf,text="清空",command=self.clear_console,bg=self.colors['accent_red'],fg='white',relief='flat').pack(side='right',padx=10)
        self.console=scrolledtext.ScrolledText(cf,bg=self.colors['console_bg'],fg=self.colors['accent_green'],font=("Consolas",10),wrap=tk.WORD)
        self.console.pack(fill='both',expand=True,pady=5)
        cmdf=tk.Frame(t,bg=self.colors['bg_light'])
        cmdf.pack(fill='x',padx=10,pady=10)
        tk.Label(cmdf,text="命令:",font=("微软雅黑",11),bg=self.colors['bg_light'],fg='white').pack(side='left',padx=5)
        self.cmd_entry=tk.Entry(cmdf,bg=self.colors['console_bg'],fg='white',font=("Consolas",11))
        self.cmd_entry.pack(side='left',padx=5,fill='x',expand=True)
        self.cmd_entry.bind('<Return>',lambda e:self.send_command())
        tk.Button(cmdf,text="发送",command=self.send_command,bg=self.colors['accent_blue'],fg='white',relief='flat',width=8).pack(side='right',padx=5)
        qf=tk.Frame(t,bg=self.colors['bg_light'])
        qf.pack(fill='x',padx=10,pady=5)
        for c in ['list','help','save-all','save-off','save-on','reload','seed','status']:
            tk.Button(qf,text=c,command=lambda cmd=c:self.quick_command(cmd),bg=self.colors['bg_medium'],fg='white',relief='flat',width=8).pack(side='left',padx=2)
    
    def setup_backup_tab(self,nb):
        t=tk.Frame(nb,bg=self.colors['bg_light'])
        nb.add(t,text="💾 备份管理")
        lf=tk.LabelFrame(t,text="备份列表",font=("微软雅黑",11,"bold"),bg=self.colors['bg_light'],fg='white',bd=2)
        lf.pack(fill='both',expand=True,padx=10,pady=10)
        tf=tk.Frame(lf,bg=self.colors['bg_light'])
        tf.pack(fill='both',expand=True,padx=5,pady=5)
        self.backup_tree=ttk.Treeview(tf,columns=("名称","大小","时间"),show='headings',height=15)
        self.backup_tree.heading("名称",text="备份名称")
        self.backup_tree.heading("大小",text="大小(MB)")
        self.backup_tree.heading("时间",text="创建时间")
        self.backup_tree.column("名称",width=250)
        self.backup_tree.column("大小",width=100)
        self.backup_tree.column("时间",width=200)
        sb=ttk.Scrollbar(tf,orient="vertical",command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=sb.set)
        self.backup_tree.pack(side='left',fill='both',expand=True)
        sb.pack(side='right',fill='y')
        bf=tk.Frame(lf,bg=self.colors['bg_light'])
        bf.pack(fill='x',padx=5,pady=5)
        tk.Button(bf,text="↩️ 回档",command=self.restore_backup,bg=self.colors['accent_yellow'],fg='white',relief='flat').pack(side='left',padx=5,expand=True,fill='x')
        tk.Button(bf,text="🗑️ 删除",command=self.delete_backup,bg=self.colors['accent_red'],fg='white',relief='flat').pack(side='left',padx=5,expand=True,fill='x')
        tk.Button(bf,text="🔄 刷新",command=self.refresh_backup_list,bg=self.colors['accent_blue'],fg='white',relief='flat').pack(side='left',padx=5,expand=True,fill='x')
    
    def setup_players_tab(self,nb):
        t=tk.Frame(nb,bg=self.colors['bg_light'])
        nb.add(t,text="👥 玩家管理")
        of=tk.LabelFrame(t,text="🟢 在线玩家",font=("微软雅黑",11,"bold"),bg=self.colors['bg_light'],fg='white',bd=2)
        of.pack(side='left',fill='both',expand=True,padx=5,pady=5)
        cf=tk.Frame(of,bg=self.colors['bg_light'])
        cf.pack(fill='x',padx=5,pady=5)
        self.online_count_label=tk.Label(cf,text="在线人数: 0",font=("微软雅黑",10,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_green'])
        self.online_count_label.pack(side='left')
        tk.Button(cf,text="🔄 刷新",command=self.refresh_players,bg=self.colors['accent_blue'],fg='white',relief='flat').pack(side='right')
        self.online_listbox=tk.Listbox(of,bg=self.colors['bg_medium'],fg=self.colors['accent_green'],font=("微软雅黑",10))
        self.online_listbox.pack(fill='both',expand=True,padx=5,pady=5)
        self.online_listbox.bind('<Double-Button-1>',lambda e:self.kick_player())
        bf=tk.Frame(of,bg=self.colors['bg_light'])
        bf.pack(fill='x',padx=5,pady=5)
        tk.Button(bf,text="👢 踢出",command=self.kick_player,bg=self.colors['accent_yellow'],fg='white',relief='flat').pack(side='left',padx=2,expand=True,fill='x')
        tk.Button(bf,text="🔨 封禁",command=self.ban_player,bg=self.colors['accent_red'],fg='white',relief='flat').pack(side='left',padx=2,expand=True,fill='x')
        tk.Button(bf,text="👑 设为OP",command=self.set_op,bg=self.colors['accent_green'],fg='white',relief='flat').pack(side='left',padx=2,expand=True,fill='x')
        bf2=tk.LabelFrame(t,text="🔴 封禁列表",font=("微软雅黑",11,"bold"),bg=self.colors['bg_light'],fg='white',bd=2)
        bf2.pack(side='right',fill='both',expand=True,padx=5,pady=5)
        self.ban_listbox=tk.Listbox(bf2,bg=self.colors['bg_medium'],fg=self.colors['accent_red'],font=("微软雅黑",9))
        self.ban_listbox.pack(fill='both',expand=True,padx=5,pady=5)
        tk.Button(bf2,text="✅ 解除封禁",command=self.unban_player,bg=self.colors['accent_green'],fg='white',relief='flat').pack(pady=5,padx=5,fill='x')
    
    def setup_invite_tab(self,nb):
        t=tk.Frame(nb,bg=self.colors['bg_light'])
        nb.add(t,text="🔗 邀请管理")
        inf=tk.LabelFrame(t,text="生成邀请码",font=("微软雅黑",11,"bold"),bg=self.colors['bg_light'],fg='white',bd=2)
        inf.pack(fill='x',padx=10,pady=10)
        cdf=tk.Frame(inf,bg=self.colors['bg_medium'],relief='ridge',bd=2)
        cdf.pack(fill='x',padx=10,pady=10)
        tk.Label(cdf,text="邀请码:",font=("微软雅黑",12),bg=self.colors['bg_medium'],fg='white').pack(side='left',padx=10)
        self.invite_code_label=tk.Label(cdf,text="未生成",font=("微软雅黑",14,"bold"),bg=self.colors['bg_medium'],fg=self.colors['accent_green'])
        self.invite_code_label.pack(side='left',padx=10)
        tk.Button(inf,text="生成新邀请码",command=self.generate_invite_code,bg=self.colors['accent_green'],fg='white',relief='flat').pack(pady=10,padx=10,fill='x')
        lkf=tk.LabelFrame(t,text="分享链接",font=("微软雅黑",11,"bold"),bg=self.colors['bg_light'],fg='white',bd=2)
        lkf.pack(fill='x',padx=10,pady=10)
        self.invite_link=tk.Entry(lkf,bg=self.colors['console_bg'],fg='white',font=("Consolas",10),readonlybackground=self.colors['console_bg'])
        self.invite_link.pack(fill='x',padx=10,pady=10)
        tk.Button(lkf,text="复制链接",command=self.copy_invite_link,bg=self.colors['accent_blue'],fg='white',relief='flat').pack(pady=5)
    
    def setup_help_tab(self,nb):
        t=tk.Frame(nb,bg=self.colors['bg_light'])
        nb.add(t,text="ℹ️ 关于")
        af=tk.Frame(t,bg=self.colors['bg_light'])
        af.pack(fill='both',expand=True,padx=20,pady=20)
        tk.Label(af,text="🎮",font=("Segoe UI",48),bg=self.colors['bg_light'],fg=self.colors['accent_green']).pack(pady=10)
        tk.Label(af,text="Minecraft 服务器专业管理器",font=("微软雅黑",20,"bold"),bg=self.colors['bg_light'],fg='white').pack(pady=5)
        tk.Label(af,text="版本 v10.0",font=("微软雅黑",12),bg=self.colors['bg_light'],fg=self.colors['text_gray']).pack()
        tk.Label(af,text="\n👑 制作：houukhhk 👑",font=("微软雅黑",14,"bold"),bg=self.colors['bg_light'],fg=self.colors['accent_purple']).pack(pady=10)
        tk.Label(af,text="这是一个专为 Minecraft Bedrock Edition 设计的服务器管理工具，提供一站式解决方案，帮助你轻松管理和维护服务器。",font=("微软雅黑",10),bg=self.colors['bg_light'],fg=self.colors['text_gray']).pack()
        tk.Label(af,text="\n✨ 新增功能：\n• 外网IP显示，方便好友远程连接\n• 作弊模式开关，一键开启/关闭\n• 快速作弊命令按钮\n• 针对特定玩家作弊",font=("微软雅黑",10),bg=self.colors['bg_light'],fg=self.colors['text_gray']).pack()
        tk.Label(af,text="\n© 2024 houukhhk. All rights reserved.",font=("微软雅黑",9),bg=self.colors['bg_light'],fg=self.colors['text_gray']).pack(pady=10)
    
    def on_closing(self):
        self.save_all_configs()
        if self.server_running: self.stop_server()
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW",self.on_closing)
        self.root.mainloop()

if __name__=="__main__":
    OnlineServerManager().run()
# Copyright (c) 2024 [houukhhk]
# Licensed under the MIT License.
# 
# Minecraft Bedrock Server (BDS) Manager & Auto-Backup Tool
# 本專案是一個獨立開發的開源工具，用於輔助管理 Minecraft Bedrock 伺服器。
# 本專案與 Mojang AB 或 Microsoft 無官方關聯。