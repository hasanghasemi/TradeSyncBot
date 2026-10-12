# Copy Trading Script

This Python script facilitates copy trading between two MetaTrader 5 accounts. Any trade placed on account 1 will be automatically copied to account 2. Similarly, when a trade is closed on account 1, it will also be closed on account 2.

# Warning
Please be aware that this script does not guarantee the successful execution of copied trades. You must test it thoroughly with a demo account before using it on a live account. I am not responsible for any potential losses or damages resulting from the use of this script.

## Features
- **Trade Mirroring:** Automatically copies trades from account 1 to account 2.
- **Selective Trade Copying:** Trades are only copied if both stop loss and take profit are set.
- **Real-time Synchronization:** Trades are mirrored in real-time, ensuring that account 2 reflects the actions taken on account 1.

## Getting Started

### Prerequisites
- MetaTrader 5 installed
- In MetaTrader 5 => Options => Expert Advisors, only **Allow algorithmic trading** and **Allow DLL imports** should be checked!

### Installation

#### Windows
1. Download and install Python from the [official website](https://www.python.org/downloads/).
2. Add Python to your system PATH during the installation.

#### Linux
1. Install Python using your distribution's package manager. For example, on Ubuntu:
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```

#### Mac
1. Download and install Python from the [official website](https://www.python.org/downloads/).
2. Alternatively, you can use Homebrew:
    ```bash
    brew install python
    ```

### Required Packages
1. Install MetaTrader 5:
    ```bash
    pip install MetaTrader5
    ```
2. Uninstall numpy and install a compatible version:
    ```bash
    pip uninstall numpy
    pip install numpy==1.26.4
    ```

### Configuration
1. After the first execution of the script, fill in the `accounts.json` file with the credentials of both MetaTrader 5 accounts:
    ```json
    {
      "account_1": {
        "login": "your_login",
        "password": "your_password",
        "server": "your_server"
      },
      "account_2": {
        "login": "your_login",
        "password": "your_password",
        "server": "your_server"
      }
    }
    ```
2. Save the `accounts.json` file.

### Usage
1. Run the script:
    ```bash
    python CopyTrading.py
    ```
2. The script will start monitoring trades on account 1 and copy them to account 2, provided that stop loss and take profit are set.

### Important Notes
- Only trades placed after starting the script will be copied. Existing trades will not be mirrored.
- Trades without stop loss and take profit will not be copied.

## Desired Features
- **Stop Loss and Take Profit Synchronization:** Automatically synchronize any changes in stop loss and take profit for copied trades.

## Acknowledgements
- MetaTrader 5
- Python Community

## Contact
For any issues or suggestions, feel free to open an issue or contact the maintainers.


## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# TradeSyncBot - MT5 Copy Trading (Dual Terminal)

A powerful and stable Python-based copy trading bot for MetaTrader 5 (MT5). This script copies trades from a Master account to a Slave account in real-time.

Unlike traditional copy trading scripts that struggle with login/logout issues on a single terminal, this version is specifically designed to use **two separate MT5 terminals** installed in different directories. This ensures maximum stability, prevents "Authorization failed" errors, and allows seamless execution.

## ✨ Features

*   **Dual Terminal Architecture:** Runs flawlessly by communicating with two separate MT5 terminals (one for Master, one for Slave).
*   **Exact Volume Copy:** Copies the exact lot size from the Master account to the Slave account.
*   **SL/TP Copy:** Copies the original Stop Loss (SL) and Take Profit (TP) from the Master trade.
*   **SL/TP Synchronization:** If you modify SL or TP on the Master trade, it automatically updates the Slave trade.
*   **Auto-Close Trades:** When a trade is closed on the Master account, the bot automatically closes the corresponding trade on the Slave account.
*   **Smart Filling Mode Handling:** Automatically detects and resolves the common `Retcode: 10030 (Unsupported filling mode)` error by trying FOK, IOC, and RETURN modes.
*   **Symbol Suffix Detection:** Automatically finds the correct symbol name on the Slave account (e.g., handling suffixes like `_i`, `.r`, `micro`, etc.).
*   **Detailed Logging:** Provides clear logs for every action, making it easy to debug and monitor.

## 📋 Prerequisites

Before running the bot, ensure you have the following:

1.  **Windows OS** (The script relies on Windows paths for MT5).
2.  **Python 3.10 or 3.11** installed. (Python 3.13 is not recommended due to package compatibility issues).
3.  **MetaTrader 5 Terminal** installed **twice** in two different directories (e.g., `C:\Program Files\LiteFinance MT5 Terminal` and `E:\Program Files\LiteFinance MT5 Terminal`).
4.  **MetaTrader5 Python Package** and **NumPy** installed. Run the following in your command prompt:
    ```bash
    pip install MetaTrader5
    pip install numpy==1.26.4
    
 Installation & Setup
Clone or Download the Repository:
Download the ZIP file of this project and extract it to a folder on your computer (e.g., C:\TradeSyncBot).

Create the Configuration File (accounts.json):
Create a file named accounts.json in the project folder and fill it with your account credentials. Note: Do not use the old "accounts": [...] format. Use the account_1 and account_2 format as shown below:

json
{
  "account_1": {
    "login": "YOUR_MASTER_LOGIN",
    "password": "YOUR_MASTER_PASSWORD",
    "server": "YOUR_MASTER_SERVER"
  },
  "account_2": {
    "login": "YOUR_SLAVE_LOGIN",
    "password": "YOUR_SLAVE_PASSWORD",
    "server": "YOUR_SLAVE_SERVER"
  }
}
Configure Terminal Paths in CopyTrading.py:
Open CopyTrading.py with a text editor and update the paths to match your installation directories:

python
# Master account (C drive)
MASTER_PATH = r"C:\Program Files\LiteFinance MT5 Terminal\terminal64.exe" 
# Slave account (E drive)
SLAVE_PATH = r"E:\Program Files\LiteFinance MT5 Terminal\terminal64.exe"  

🎮 How to Run
Open Both MT5 Terminals:

Open the Master terminal (C drive) and log in to your Master account.

Open the Slave terminal (E drive) and log in to your Slave account.

Enable Algo Trading:

In both terminals, click the "Algo Trading" button in the top toolbar so it turns green.

Run the Script:

Open a Command Prompt (CMD) in the project folder.

Run the following command:

bash
python CopyTrading.py
Confirm Setup:

The bot will connect to the Slave terminal first.

Once connected, it will ask you to confirm Algo Trading is enabled. Press Enter to start monitoring.

Test:

Open a new trade on your Master account. The bot will detect it and copy it to the Slave account with the same volume, SL, and TP.

⚠️ Important Notes & Troubleshooting
Security Warning: The accounts.json file contains your passwords. NEVER upload this file to GitHub. Ensure it is listed in your .gitignore file.

Filling Mode Error (10030): If you see this error, don't worry. The script is designed to automatically retry with different filling modes.

Symbol Suffix: If your broker uses different symbol names (e.g., EURUSD vs EURUSD_i), the script will try to find the correct one automatically.

Stability: Ensure both MT5 terminals remain open and your internet connection is stable during operation.

📜 Disclaimer
This bot is provided for educational purposes. Trading involves significant risk. Use this bot at your own risk. The developers are not responsible for any financial losses incurred.



    
