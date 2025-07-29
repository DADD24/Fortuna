Dash Casino ApplicationThis project is a web-based casino application built with Python's Dash framework and a PostgreSQL database. It serves as a demonstration of full-stack application development, including database management with Docker, backend business logic, and a reactive user interface.FeaturesUser System: Simple email/username login and registration.Wallet: Add mock credit cards and purchase in-game tokens.Slots Game: A classic 3-reel slot machine game.Food Station: A virtual concession stand to spend tokens.Database Integration: All user data, transactions, and game history are stored in a PostgreSQL database.Project Structurecasino_project/
├── docker-compose.yml   # Defines the PostgreSQL service
├── postgres/
│   └── init.sql         # Initializes the database schema and default data
├── app.py               # The main Dash application file
├── requirements.txt     # Python dependencies
└── README.md            # This file
Getting StartedFollow these instructions to get the application running on your local machine.PrerequisitesDocker and Docker Compose: Required to run the PostgreSQL database. Install Docker.Python 3.8+: Required to run the Dash application.pip: Python's package installer.Installation & SetupClone the Repository (or create the files):Create a directory named casino_project and place all the files from this document into it, following the structure outlined above.Start the Database:Navigate to the root of the casino_project directory in your terminal and run the following command:docker-compose up -d
This command will start the PostgreSQL container in detached mode. The database will be running on localhost:5432. The init.sql script will automatically run to set up the necessary tables.Set up a Python Virtual Environment (Recommended):It's best practice to use a virtual environment to manage project dependencies.# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install Python Dependencies:With your virtual environment activated, install the required packages.pip install -r requirements.txt
Run the Application:Once the dependencies are installed, you can start the Dash application.python app.py
The application will be available at http://localhost:8050 in your web browser.How to Use the AppLogin: Open the app in your browser. You'll be prompted to enter an email and username. If the combination is new, a new user will be created.Navigate: Use the tabs at the top to switch between the Slots game, your Wallet, and the Food Station.Add Funds: Go to the Wallet tab to add a mock credit card and purchase tokens.Play: Go to the Slots tab, set your bet, and spin the reels!Enjoy: Use your winnings at the Food Station.