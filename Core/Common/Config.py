import configparser
import os

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.config.read(self.config_file)

    def get_value(self, section, option, fallback=None):
        """获取配置值"""
        try:
            # 每次读取前重新加载配置文件，确保获取最新值
            self.config.read(self.config_file, encoding='utf-8')
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def set_value(self, section, option, value):
        """设置配置值"""
        # 确保section存在
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        # 设置值
        self.config.set(section, option, str(value))
        
        # 保存到文件
        self.save_config()

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            raise

    def get_lottery_config(self):
        """获取抽奖配置"""
        return {
            'points': int(self.get_value('Lottery', 'points', '1'))
        }

    def update_lottery_config(self, config_data):
        """更新抽奖配置"""
        # 只处理 lotteryPoints 参数
        if 'lotteryPoints' in config_data:
            self.set_value('Lottery', 'points', config_data['lotteryPoints'])