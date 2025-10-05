# **☕・Virtual Coffee Machine Simulation**

### **Ever Dreamed of Making Your Own Coffee Machine? ✨**

Welcome to our Virtual Coffee Machine Simulation! This awesome project is your magical bridge to understanding computational thinking through a real-world coffee machine simulation. Think of it as bringing your coffee dreams to life with code! No more just thinking about algorithms – let's make them _brew_ things!

---

### **📋・Table of Contents**

- **✨・<a href="#what-is-coffee-machine" style="text-decoration: none;">What is Coffee Machine Simulation?</a>**
- **🛠️・<a href="#getting-started" style="text-decoration: none;">Getting Started</a>**
- **⚙️・<a href="#setup-database" style="text-decoration: none;">Setup Google Sheets Database</a>**
- **🗺️・<a href="#how-to-use" style="text-decoration: none;">How to Use</a>**
- **🚀・<a href="#features" style="text-decoration: none;">Amazing Features</a>**
- **🆕・<a href="#new" style="text-decoration: none;">What’s New in Term 2 (Improvements)</a>**
- **📊・<a href="#computational-thinking" style="text-decoration: none;">Computational Thinking Applied</a>**
- **💖・<a href="#contributing" style="text-decoration: none;">Contributing</a>**
- **📜・<a href="#license" style="text-decoration: none;">License</a>**
- **👋・<a href="#about-us" style="text-decoration: none;">About Us!</a>**

---

### <div id="what-is-coffee-machine">**✨・What is Coffee Machine Simulation?**</div>

Our Virtual Coffee Machine Simulation is a super cool project designed to demonstrate computational thinking principles through a real-world coffee machine experience! 🚀 This is our **final project** for the **Computational Thinking** course at **Institut Teknologi Bandung (ITB)**, specifically for the **Matriculation Program** ("Tahap Persiapan Bersama").

The simulation features:
- 🌐・**Google Sheets Integration** as a live database
- 🛒・**Multi-order Management** system  
- 💳・**Multiple Payment Methods** (Cash & QRIS)
- 📱・**QR Code Integration** for order confirmation
- 🔐・**Admin Panel** with secure authentication
- 🎯・**Real-time Stock Management**

Get ready to see computational thinking in action through coffee brewing! ☕✨

---

### <div id="getting-started">**🛠️・Getting Started (Let's Brew Some Coffee! ☕)**</div>

Ready to bring your coffee machine to life? Here's how to get our simulation up and running in a flash:

1.  **Clone the magic!** ✨
    
    ```bash
    git clone https://github.com/ZulfaNurhuda/CoffeeMachine.project.git
    cd CoffeeMachine.project
    ```

2.  **Set Up Python Virtual Environment** 🐍

    ```bash
    # Navigate to the src directory
    cd src

    # Create virtual environment
    python -m venv CoffeeMachine.env
    
    # Activate virtual environment
    # On Windows:
    CoffeeMachine.env\Scripts\activate
    # On macOS/Linux:
    source CoffeeMachine.env/bin/activate
    ```

3.  **Install Dependencies** 📦

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables** 🔐

    ```bash
    # Copy environment template
    cp credentials/.env.example credentials/.env
    ```

    Edit the `.env` file with your Google Sheets credentials (see next section for detailed setup).

---

### <div id="setup-database">**⚙️・Setup Google Sheets Database (The Heart of Our Coffee Machine! 📊)**</div>

Our coffee machine uses Google Sheets as its live database! Here's how to set it up:

#### **Get the Database Template**

1. **Visit our Database Template**: **<a href="https://docs.google.com/spreadsheets/d/1aIdU_E6X5ZI0xcS6caC1SfajpIycn97aed0or6YxxXM" style="text-decoration: none;">Coffee Machine Database Template</a>**
2. **Make a Copy**: Click **"File" → "Make a copy"** to create your own version
3. **Note the Spreadsheet ID**: Copy the long string between `/d/` and `/edit` in your new spreadsheet URL

#### **Database Structure**

Our spreadsheet contains these essential sheets:
- **`PersediaanKopi`**: Coffee types, prices, and stock information
- **`PersediaanTambahan`**: Additional ingredients and their stock levels  
- **`ReferenceID`**: Reference data and ID mappings
- **`AntrianPesananQR`**: QR code order queue and online order management
- **`DataPenjualan`**: Sales transaction records and order history

#### **Create Google Service Account**

1. **Go to Google Cloud Console**: Visit [console.cloud.google.com](https://console.cloud.google.com/)
2. **Create New Project**: Click "Select a project" → "New Project" → Enter project name → "Create"
3. **Enable Google Sheets API**: Go to "APIs & Services" → "Library" → Search "Google Sheets API" → "Enable"
4. **Create Service Account**: "APIs & Services" → "Credentials" → "Create Credentials" → "Service Account"
5. **Generate JSON Key**: Click your service account → "Keys" → "Add Key" → "Create New Key" → Choose "JSON"
6. **Save Credentials**: Save the downloaded file as `credentials.json` in `credentials/`
7. **Share Spreadsheet**: Open your spreadsheet → "Share" → Add service account email → Give "Editor" permissions

#### **Configure Environment Variables**

Edit your `.env` file:

```env
# Path/file name of your service account json inside src/credentials
FILE_AKUN_LAYANAN=credentials.json
# Google Spreadsheet ID (string between /d/ and /edit)
ID_SHEET=your_sheet_id
```

---

### <div id="how-to-use">**🗺️・How to Use (Your Coffee Journey! ☕)**</div>

Once everything is set up, you're just one command away from brewing virtual coffee!

You can run from the repository root or from `src`:

```bash
cd src
python main.py
```

Then follow the interactive menu to:
1. **Browse Menu**: View available coffee options with real-time stock
2. **Place Orders**: Select coffee, customize composition, choose quantity  
3. **Pick Temperature**: Hot or cold - your choice!
4. **Make Payment**: Choose between cash or QRIS payment
5. **QR Confirmation (Web)**: For QRIS, scan the ASCII QR shown to open the local page and confirm payment
6. **Scan Online Order**: Use menu "Scan QR" to process website orders from the sheet queue
7. **Admin Access**: Use admin code for restocking and system management

Notes:
- The app starts a local web service in the background at `http://0.0.0.0:5000` for QR confirmation pages.
- Input prompts time out after 60s and return to the main menu automatically.

---

### <div id="features">**🚀・Amazing Features**</div>

Our coffee machine simulation is packed with incredible features:

- **🌐 Google Sheets Integration**: Real-time database connectivity
- **🛒 Multi-Order Management**: Handle multiple orders simultaneously
- **🎛️ Customizable Menu**: Dynamic menu based on available data
- **🌡️ Temperature Selection**: Choose between hot and cold beverages
- **🧂 Custom Composition**: Adjust sugar, milk, creamer, chocolate
- **💳 Dual Payment System**: Cash and QRIS payment methods
- **📱 QR Code Integration**: QRIS checkout with ASCII QR and local confirmation page
- **📊 Detailed Order Recording**: Comprehensive transaction logging
- **🛡️ Error Handling**: Robust error management system
- **ℹ️ User-Friendly Interface**: Clear information at every step
- **✅ Input Validation**: Comprehensive user input validation
- **🔐 Admin Panel**: Secure admin menu with authentication

### <div id="new">**🆕・What's New in Term 2 (Improvements)**</div>

- **Modular Architecture**: Clean separation into `apps/` packages (menu, orders, payments, admin, DB, webservice, utils).
- **Background Web Service**: Flask server runs alongside CLI for QR confirmations (`/search`, `/proses_cari`, `/berhasil`, `/gagal`).
- **QRIS Flow Upgrade**: ASCII QR encodes a local URL; visiting the page updates status to "Selesai" automatically.
- **📱 Online Order Scanner (Webcam QR Scanning)**: Revolutionary new "Scan QR" menu feature that uses your webcam with OpenCV to scan QR codes from online orders! Process orders from the `AntrianPesananQR` queue automatically, intelligently handles partial inventory fills, and updates Google Sheets in real-time. Perfect for bridging online orders to your physical coffee machine! 🎥✨
- **Input Timeout UX**: Prompts auto-cancel after 60s and return to main menu.
- **Bestseller Highlight**: Menu marks most sold coffee (★) derived from `DataPenjualan`.
- **Queued + Periodic Sync**: Batched cache updates to Sheets in the background, with safe synchronous paths for admin restock and admin code persistence (`credentials/admin_code.txt`).
- **Graceful Shutdown**: CTRL+C triggers a final sync to persist pending updates.

---

### <div id="computational-thinking">**📊・Computational Thinking Applied (The Magic Behind the Code! 🧠)**</div>

This project demonstrates key computational thinking principles in action:

- **🧩 Decomposition**: Breaking down coffee ordering into smaller, manageable tasks (selection → customization → payment → confirmation)
- **🔍 Pattern Recognition**: Identifying common user behaviors and system patterns throughout the ordering process
- **🎯 Abstraction**: Simplifying complex real-world coffee machine operations into clean, understandable code structures
- **⚙️ Algorithm Design**: Creating step-by-step procedures for order processing, payment validation, and stock management
- **🔄 Iteration**: Implementing loops for menu displays, order processing cycles, and user interactions
- **📊 Data Structures**: Organizing information efficiently using lists, dictionaries, and objects for orders and coffee data

Get ready to see computational thinking brew some amazing results! ☕✨

---

### <div id="about-us">**👋・About Us!**</div>

**GROUP 13 - CLASS 31, COMPUTATIONAL THINKING course**
- **Laurenisus Dani Rendragraha** (19624272)  
- **Mineva Azzahra** (19624227)  
- **Muhammad Faiz Alfada Dharma** (19624244)  
- **Muhammad Zulfa Fauzan Nurhuda** (19624258)  

Just regular students studying Computational Thinking at ITB! 😄 Always excited to learn and build cool stuff through code! We're passionate about applying computational thinking principles to solve real-world problems, one virtual coffee at a time! ☕🚀

<img src="https://i.imgur.com/Zp8msEG.png" alt="Logo ITB" height="90" style="border-radius: 10px">