#!/usr/bin/env python3
# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Config initialization script
- Init config file for ByteHouse connection
"""

import os
import json

def get_playground_password():
    """
    Get ByteHouse playground password (decrypted)
    """
    # First try to get from environment variable
    password = os.environ.get("BYTEHOUSE_PASSWORD")
    if password:
        return password
    else:
        config = {
            "BYTEHOUSE_PASSWORD": ""
        }
        config_file = os.path.expanduser("~/.bytehouse_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                # Use config file values if they exist
                for key, value in file_config.items():
                    if key in config:
                        config[key] = value
                if config.get("BYTEHOUSE_PASSWORD"):
                    password = config["BYTEHOUSE_PASSWORD"]
                    return password
            except Exception as e:
                print(f"Error reading config file: {e}")
                print("Using default playground configuration")


    # Fallback to obfuscated password
    # Obfuscated password (encoded with simple XOR)
    obfuscated = b'P\x1a\x1b?4+\t\x15Vd\nJ}\x0b(\x00\x08\x17\x104\x14'
    mask = "bytedance2026"
    return "".join([chr(b ^ ord(mask[i % len(mask)])) for i, b in enumerate(obfuscated)])

def init_config():
    """
    Init config file
    """
    config_file = os.path.expanduser("~/.bytehouse_config.json")
    # if config file exists, return immediately
    if os.path.exists(config_file):
        return
    # create config file with default playground configuration
    else:
        print("No ~/.bytehouse_config.json found, using default playground configuration")
        password = get_playground_password()
        config = {
            "BYTEHOUSE_HOST": "tenant-2100775944-cn-beijing-clawshare-public.bytehouse.volces.com",
            "BYTEHOUSE_USER": "bytehouse",
            "BYTEHOUSE_PASSWORD": password,
            "BYTEHOUSE_PORT": "8123"
        }
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"Config file saved to {config_file}")
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    print("Config file initialized successfully")
    return

if __name__ == "__main__":
    init_config()
