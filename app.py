# app.py
# This is the main application file.
# It contains the Dash layout and all the business logic for the casino.

import os
import random
import time

import dash
import dash_bootstrap_components as dbc
import psycopg2
import psycopg2.extras
from dash import dcc, html, Input, no_update, Output, State

# --- Database Configuration ---
# It's good practice to retry the connection to give the DB container time to start.
time.sleep(5)  # A simple delay to wait for the DB to initialize.
try:
    conn = psycopg2.connect(
        dbname="casino_db",
        user="casino_user",
        password="casino_password",
        host="localhost",  # Use 'db' if running this app in a docker container in the same network
        port="5432",
    )
except psycopg2.OperationalError as e:
    print(f"Could not connect to database: {e}")
    # In a real app, you'd have more robust retry logic.
    exit()

# --- Dash App Initialization ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)
app.title = "Dash Casino"


# --- Helper Functions ---
def get_user(user_id):
    """Fetches user data from the database."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        return cur.fetchone()


def get_user_by_email_username(email, username):
    """Fetches a user by their email and username."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT * FROM users WHERE email = %s AND username = %s;", (email, username)
        )
        return cur.fetchone()


def create_user(email, username):
    """Creates a new user and returns their data."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "INSERT INTO users (email, username) VALUES (%s, %s) RETURNING *;",
            (email, username),
        )
        conn.commit()
        return cur.fetchone()


def get_user_cards(user_id):
    """Fetches all credit cards for a given user."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT id, card_number FROM credit_cards WHERE user_id = %s;", (user_id,)
        )
        return cur.fetchall()


def get_food_menu():
    """Fetches the entire food menu."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM food_menu ORDER BY price;")
        return cur.fetchall()


# --- App Layout ---
app.layout = html.Div(
    [
        # Store for user session data (user_id)
        dcc.Store(id="user-session", storage_type="local"),
        # Header
        html.Div(
            className="text-center p-4 bg-primary text-white",
            children=[
                html.H1("Welcome to the Dash Casino"),
                html.P("A demonstration of SQL databases and business logic."),
            ],
        ),
        # Main content area with tabs
        dbc.Container(
            id="main-content",
            className="mt-4",
            fluid=True,
            children=[
                # Placeholder for content, will be updated by callbacks
            ],
        ),
        # Notification area
        html.Div(
            id="notification-toast-container",
            style={"position": "fixed", "top": 66, "right": 10, "zIndex": 1050},
        ),
    ]
)

# --- Content Layouts ---


def create_login_layout():
    """Returns the layout for the login screen."""
    return dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("User Login / Sign Up")),
                    dbc.CardBody(
                        [
                            dbc.Input(
                                id="login-email",
                                placeholder="Enter your email...",
                                type="email",
                                className="mb-3",
                            ),
                            dbc.Input(
                                id="login-username",
                                placeholder="Enter your username...",
                                type="text",
                                className="mb-3",
                            ),
                            dbc.Button(
                                "Login / Register",
                                id="login-button",
                                color="success",
                                className="w-100",
                            ),
                        ]
                    ),
                ]
            ),
            width={"size": 6, "offset": 3},
        ),
        className="mt-5",
    )


def create_main_layout(user_data):
    """Returns the main application layout after login."""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.H3(f"Welcome, {user_data['username']}!"), width=8),
                    dbc.Col(
                        html.Div(
                            [
                                html.Strong("Tokens: "),
                                html.Span(
                                    user_data["tokens"], id="user-tokens-display"
                                ),
                            ]
                        ),
                        width=3,
                        className="text-end fs-4",
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Logout", id="logout-button", color="danger", size="sm"
                        ),
                        width=1,
                    ),
                ]
            ),
            html.Hr(),
            dbc.Tabs(
                id="app-tabs",
                active_tab="tab-slots",
                children=[
                    dbc.Tab(label="Slots", tab_id="tab-slots"),
                    dbc.Tab(label="Blackjack", tab_id="tab-blackjack"),
                    dbc.Tab(label="Wallet", tab_id="tab-wallet"),
                    dbc.Tab(label="Food Station", tab_id="tab-food"),
                    dbc.Tab(label="History", tab_id="history-tab"),
                ],
            ),
            html.Div(id="tab-content", className="p-4"),
        ]
    )


# --- Callbacks ---


@app.callback(Output("main-content", "children"), Input("user-session", "data"))
def render_main_content(user_id):
    """Renders the main content based on whether the user is logged in."""
    if user_id:
        user_data = get_user(user_id)
        if user_data:
            return create_main_layout(user_data)
    return create_login_layout()


@app.callback(
    Output("user-session", "data", allow_duplicate=True),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-username", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, email, username):
    """Handles the user login/registration process."""
    if not email or not username:
        toast = dbc.Toast(
            "Email and username are required.",
            header="Login Error",
            icon="danger",
            duration=4000,
        )
        return no_update, toast

    user = get_user_by_email_username(email, username)
    if not user:
        user = create_user(email, username)
        toast_message = "New user created successfully!"
        toast_header = "Welcome!"
        toast_icon = "success"
    else:
        toast_message = f"Welcome back, {user['username']}!"
        toast_header = "Login Successful"
        toast_icon = "success"

    toast = dbc.Toast(
        toast_message, header=toast_header, icon=toast_icon, duration=4000
    )
    return user["id"], toast


@app.callback(
    Output("user-session", "data"),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    """Logs the user out by clearing the session data."""
    if n_clicks is None:
        return no_update
    return None  # Setting data to None effectively logs them out


@app.callback(
    Output("tab-content", "children"),
    Input("app-tabs", "active_tab"),
    State("user-session", "data"),
)
def render_tab_content(active_tab, user_id):
    """Renders the content for the selected tab."""
    if not user_id:
        return "Please log in to see content."
    if active_tab == "tab-wallet":
        return render_wallet_tab(user_id)
    elif active_tab == "tab-slots":
        return render_slots_tab(user_id)
    elif active_tab == "tab-blackjack":
        return render_blackjack_tab(user_id)
    elif active_tab == "tab-food":
        return render_food_tab(user_id)
    elif active_tab == "history-tab":
        return render_history_tab(user_id)
    return html.P("This is the content of the selected tab.")


# --- Wallet Tab ---
def render_wallet_tab(user_id):
    cards = get_user_cards(user_id)
    card_list = (
        [
            dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}")
            for card in cards
        ]
        if cards
        else [dbc.ListGroupItem("No cards on file.")]
    )

    return html.Div(
        [
            dbc.Row(
                [
                    # Add Credit Card
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Add a New Credit Card"),
                                dbc.CardBody(
                                    [
                                        dbc.Input(
                                            id="new-card-number",
                                            placeholder="Enter 16-digit card number",
                                            type="text",
                                            maxLength=16,
                                            minLength=16,
                                        ),
                                        dbc.Button(
                                            "Add Card",
                                            id="add-card-button",
                                            color="primary",
                                            className="mt-3 w-100",
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        md=6,
                    ),
                    # View Cards
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Your Credit Cards"),
                                dbc.CardBody(
                                    dbc.ListGroup(card_list, id="card-list-group")
                                ),
                            ]
                        ),
                        md=6,
                    ),
                ]
            ),
            html.Hr(className="my-4"),
            # Purchase Tokens
            dbc.Card(
                [
                    dbc.CardHeader("Purchase Tokens"),
                    dbc.CardBody(
                        [
                            html.P("Select a credit card and an amount to purchase."),
                            dbc.Select(
                                id="card-select-dropdown",
                                options=[
                                    {
                                        "label": f"Card ending in {c['card_number'][-4:]}",
                                        "value": c["id"],
                                    }
                                    for c in cards
                                ],
                                placeholder="Select a card...",
                            ),
                            html.Div(
                                className="d-grid gap-2 d-md-flex justify-content-md-start mt-3",
                                children=[
                                    dbc.Button(
                                        "Buy 100 Tokens",
                                        id={"type": "buy-tokens-btn", "amount": 100},
                                        color="success",
                                    ),
                                    dbc.Button(
                                        "Buy 500 Tokens",
                                        id={"type": "buy-tokens-btn", "amount": 500},
                                        color="success",
                                    ),
                                    dbc.Button(
                                        "Buy 1000 Tokens",
                                        id={"type": "buy-tokens-btn", "amount": 1000},
                                        color="success",
                                    ),
                                ],
                            ),
                        ]
                    ),
                ]
            ),
            # Convert Tokens to Cash
            dbc.Card(
                [
                    dbc.CardHeader("Convert Tokens to Cash"),
                    dbc.CardBody(
                        [
                            html.P(
                                "You can convert tokens back to cash at a 1:1 rate."
                            ),
                            dbc.Input(
                                id="convert-tokens-input",
                                type="number",
                                placeholder="Enter token amount",
                                min=1,
                                step=1,
                            ),
                            dbc.Button(
                                "Convert",
                                id="convert-tokens-button",
                                color="danger",
                                className="mt-3 w-100",
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )


@app.callback(
    Output("card-list-group", "children"),
    Output("card-select-dropdown", "options"),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input("add-card-button", "n_clicks"),
    State("user-session", "data"),
    State("new-card-number", "value"),
    prevent_initial_call=True,
)
def add_credit_card(n_clicks, user_id, card_number):
    """Adds a new credit card for the user."""
    if not card_number:
        cards = get_user_cards(user_id)
        card_list = [
            dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}")
            for card in cards
        ]
        card_options = [
            {"label": f"Card ending in {c['card_number'][-4:]}", "value": c["id"]}
            for c in cards
        ]

        return card_list, card_options, no_update

    if not card_number.isdigit() or len(card_number) != 16:
        toast = dbc.Toast(
            "Please enter a valid 16-digit card number.",
            header="Error",
            icon="danger",
            duration=4000,
        )
        return no_update, no_update, toast

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO credit_cards (user_id, card_number) VALUES (%s, %s);",
            (user_id, card_number),
        )
        conn.commit()

    cards = get_user_cards(user_id)
    card_list = [
        dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}")
        for card in cards
    ]
    card_options = [
        {"label": f"Card ending in {c['card_number'][-4:]}", "value": c["id"]}
        for c in cards
    ]
    toast = dbc.Toast(
        "Credit card added successfully!",
        header="Success",
        icon="success",
        duration=4000,
    )

    return card_list, card_options, toast


@app.callback(
    Output("user-tokens-display", "children", allow_duplicate=True),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input({"type": "buy-tokens-btn", "amount": dash.ALL}, "n_clicks"),
    State("user-session", "data"),
    State("card-select-dropdown", "value"),
    prevent_initial_call=True,
)
def buy_tokens(n_clicks, user_id, card_id):
    """Handles token purchase logic."""
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return no_update, no_update

    if not card_id:
        toast = dbc.Toast(
            "Please add a credit card first.",
            header="Error",
            icon="warning",
            duration=4000,
        )
        return no_update, toast

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    amount_to_buy = eval(button_id)["amount"]

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Add tokens to user
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (amount_to_buy, user_id),
        )
        new_balance = cur.fetchone()["tokens"]
        # Log transaction
        cur.execute(
            "INSERT INTO transactions (user_id, card_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s, %s);",
            (
                user_id,
                card_id,
                "purchase_tokens",
                amount_to_buy,
                f"Purchased {amount_to_buy} tokens.",
            ),
        )
        conn.commit()

    toast = dbc.Toast(
        f"Successfully purchased {amount_to_buy} tokens!",
        header="Purchase Complete",
        icon="success",
        duration=4000,
    )
    return new_balance, toast


# callback for token conversion
@app.callback(
    Output("user-tokens-display", "children", allow_duplicate=True),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input("convert-tokens-button", "n_clicks"),
    State("convert-tokens-input", "value"),
    State("user-session", "data"),
    prevent_initial_call=True,
)
def convert_tokens(n_clicks, token_amount, user_id):
    if not token_amount or token_amount <= 0:
        toast = dbc.Toast(
            "Please enter a valid token amount.",
            header="Invalid Input",
            icon="danger",
            duration=4000,
        )
        return no_update, toast

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT tokens FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()

        if user["tokens"] < token_amount:
            toast = dbc.Toast(
                "You don't have enough tokens.",
                header="Insufficient Tokens",
                icon="warning",
                duration=4000,
            )
            return no_update, toast

        cur.execute(
            "UPDATE users SET tokens = tokens - %s WHERE id = %s RETURNING tokens;",
            (token_amount, user_id),
        )
        new_balance = cur.fetchone()["tokens"]
        cur.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
            (
                user_id,
                "convert_to_cash",
                -token_amount,
                f"Converted {token_amount} tokens to cash.",
            ),
        )
        conn.commit()

    toast = dbc.Toast(
        f"Converted {token_amount} tokens into cash!",
        header="Success",
        icon="success",
        duration=4000,
    )
    return new_balance, toast


# --- Slots Tab ---
def render_slots_tab(user_id):
    """Renders the layout for the slots game."""
    return dbc.Card(
        dbc.CardBody(
            [
                dcc.Store(id="card-select-dropdown", storage_type="local"),
                html.H4("Slot Machine", className="card-title text-center"),
                html.P("Place your bet and pull the lever!", className="text-center"),
                # Reels Display
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                "?",
                                id="reel-1",
                                className="fs-1 text-center p-4 border rounded bg-light text-dark",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            html.Div(
                                "?",
                                id="reel-2",
                                className="fs-1 text-center p-4 border rounded bg-light text-dark",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            html.Div(
                                "?",
                                id="reel-3",
                                className="fs-1 text-center p-4 border rounded bg-light text-dark",
                            ),
                            width=4,
                        ),
                    ],
                    className="mb-4",
                ),
                # Bet Amount
                dbc.InputGroup(
                    [
                        dbc.InputGroupText("Bet Amount"),
                        dbc.Input(
                            id="bet-amount", type="number", value=10, min=1, step=1
                        ),
                    ],
                    className="mb-3",
                ),
                # Spin Button
                dbc.Button(
                    "Spin!",
                    id="spin-button",
                    color="warning",
                    size="lg",
                    className="w-100",
                ),
                # Result Message
                html.Div(
                    id="spin-result-message", className="mt-3 text-center fs-4 fw-bold"
                ),
            ]
        )
    )


@app.callback(
    Output("reel-1", "children"),
    Output("reel-2", "children"),
    Output("reel-3", "children"),
    Output("spin-result-message", "children"),
    Output("user-tokens-display", "children"),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input("spin-button", "n_clicks"),
    State("user-session", "data"),
    State("bet-amount", "value"),
    prevent_initial_call=True,
)
def play_slots(n_clicks, user_id, bet_amount):
    """Handles the logic for a single spin of the slot machine."""
    if n_clicks is None:
        return no_update, no_update, no_update, no_update, no_update, no_update

    if not bet_amount or bet_amount <= 0:
        toast = dbc.Toast(
            "Bet amount must be greater than 0.",
            header="Invalid Bet",
            icon="danger",
            duration=4000,
        )
        return no_update, no_update, no_update, no_update, no_update, toast

    user = get_user(user_id)
    if user["tokens"] < bet_amount:
        toast = dbc.Toast(
            "Not enough tokens for this bet.",
            header="Insufficient Funds",
            icon="warning",
            duration=4000,
        )
        return no_update, no_update, no_update, no_update, no_update, toast

    # --- Game Logic ---
    symbols = ["🍒", "🍋", "🍊", "🔔", "BAR", "7️⃣"]
    weights = [0.3, 0.25, 0.2, 0.15, 0.08, 0.02]  # Cherry is most common, 7 is rarest
    payouts = {"🍒": 2, "🍋": 3, "🍊": 5, "🔔": 10, "BAR": 25, "7️⃣": 100}

    reels = [random.choices(symbols, weights=weights, k=1)[0] for _ in range(3)]
    is_win = reels[0] == reels[1] == reels[2]
    payout_amount = 0
    token_change = -bet_amount
    result_message = ""

    if is_win:
        winning_symbol = reels[0]
        payout_multiplier = payouts[winning_symbol]
        payout_amount = bet_amount * payout_multiplier
        token_change += payout_amount
        result_message = f"JACKPOT! You won {payout_amount} tokens!"
        result_style = {"color": "gold"}
    else:
        result_message = "Better luck next time!"
        result_style = {"color": "white"}

    # --- Database Update ---
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Update user tokens
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (token_change, user_id),
        )
        new_balance = cur.fetchone()["tokens"]
        # Log the spin
        cur.execute(
            "INSERT INTO slots_spins (user_id, bet_amount, reels, is_win, payout_amount) VALUES (%s, %s, %s, %s, %s);",
            (user_id, bet_amount, "-".join(reels), is_win, payout_amount),
        )
        # Log into transactions table
        cur.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
            (
                user_id,
                "slot_win" if is_win else "slot_loss",
                token_change,
                result_message,
            ),
        )
        conn.commit()

    return (
        reels[0],
        reels[1],
        reels[2],
        html.Span(result_message, style=result_style),
        new_balance,
        no_update,
    )


# --- Blackjack Helper Functions ---
def create_deck():
    """Creates a standard 52-card deck."""
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    return [{"rank": rank, "suit": suit} for suit in suits for rank in ranks]


def get_card_value(card, current_score=0):
    """Returns the value of a card in blackjack."""
    if card["rank"] in ["J", "Q", "K"]:
        return 10
    elif card["rank"] == "A":
        # Ace is 11 unless it would bust, then it's 1
        return 11 if current_score + 11 <= 21 else 1
    else:
        return int(card["rank"])


def calculate_hand_value(hand):
    """Calculates the total value of a hand, handling Aces properly."""
    value = 0
    aces = 0

    for card in hand:
        if card["rank"] == "A":
            aces += 1
            value += 11
        elif card["rank"] in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card["rank"])

    # Convert Aces from 11 to 1 if needed
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1

    return value


def can_split_hand(hand):
    """Check if a hand can be split (two cards of same rank)."""
    if len(hand) != 2:
        return False

    # Get the rank values for comparison
    rank1 = hand[0]["rank"]
    rank2 = hand[1]["rank"]

    # Treat all 10-value cards as equivalent for splitting
    value1 = 10 if rank1 in ["10", "J", "Q", "K"] else rank1
    value2 = 10 if rank2 in ["10", "J", "Q", "K"] else rank2

    return value1 == value2


def can_double_down(hand):
    """Check if a hand can be doubled down (exactly 2 cards)."""
    return len(hand) == 2


def format_card(card):
    """Formats a card for display."""
    return f"{card['rank']}{card['suit']}"


def format_hand(hand):
    """Formats a hand for display."""
    return " ".join([format_card(card) for card in hand])


# --- Blackjack Tab ---
def render_blackjack_tab(user_id):
    """Renders the layout for the blackjack game."""
    return dbc.Card(
        dbc.CardBody(
            [
                dcc.Store(
                    id="blackjack-game-state",
                    data={
                        "deck": [],
                        "dealer_hand": [],
                        "hands": [],  # List of player hands (supports multiple for splits)
                        "current_hand": 0,  # Index of currently active hand
                        "round_id": None,
                        "game_active": False,
                        "dealer_turn": False,
                        "initial_bet": 0,
                    },
                ),
                html.H4("Blackjack", className="card-title text-center"),
                html.P(
                    "Beat the dealer to 21! Split pairs and double down for bigger wins!",
                    className="text-center",
                ),
                # Dealer's Hand
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H5("Dealer's Hand", className="text-center"),
                                html.Div(
                                    id="dealer-hand-display",
                                    className="fs-4 text-center p-3 border rounded bg-light text-dark mb-2",
                                ),
                                html.Div(
                                    id="dealer-score-display",
                                    className="text-center fw-bold",
                                ),
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Player's Hands (dynamic, supports multiple for splits)
                html.Div(id="player-hands-container"),
                # Bet Amount
                dbc.InputGroup(
                    [
                        dbc.InputGroupText("Bet Amount"),
                        dbc.Input(
                            id="blackjack-bet-amount",
                            type="number",
                            value=10,
                            min=1,
                            step=1,
                        ),
                    ],
                    className="mb-3",
                ),
                # Game Controls
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Deal",
                                    id="deal-button",
                                    color="success",
                                    size="lg",
                                    className="w-100 mb-2",
                                ),
                                dbc.Button(
                                    "Hit",
                                    id="hit-button",
                                    color="warning",
                                    size="lg",
                                    className="w-100 mb-2",
                                    disabled=True,
                                ),
                                dbc.Button(
                                    "Stand",
                                    id="stand-button",
                                    color="danger",
                                    size="lg",
                                    className="w-100 mb-2",
                                    disabled=True,
                                ),
                                dbc.Button(
                                    "Double Down",
                                    id="double-button",
                                    color="info",
                                    size="lg",
                                    className="w-100 mb-2",
                                    disabled=True,
                                ),
                                dbc.Button(
                                    "Split",
                                    id="split-button",
                                    color="primary",
                                    size="lg",
                                    className="w-100 mb-2",
                                    disabled=True,
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                # Game Status
                html.Div(id="blackjack-status", className="mt-3 text-center fs-5"),
                # Game Result
                html.Div(
                    id="blackjack-result-message",
                    className="mt-3 text-center fs-4 fw-bold",
                ),
            ]
        )
    )


@app.callback(
    Output("blackjack-game-state", "data"),
    Output("player-hands-container", "children"),
    Output("dealer-hand-display", "children"),
    Output("dealer-score-display", "children"),
    Output("deal-button", "disabled"),
    Output("hit-button", "disabled"),
    Output("stand-button", "disabled"),
    Output("double-button", "disabled"),
    Output("split-button", "disabled"),
    Output("blackjack-status", "children"),
    Output("blackjack-result-message", "children"),
    Output("user-tokens-display", "children", allow_duplicate=True),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input("deal-button", "n_clicks"),
    Input("hit-button", "n_clicks"),
    Input("stand-button", "n_clicks"),
    Input("double-button", "n_clicks"),
    Input("split-button", "n_clicks"),
    State("blackjack-game-state", "data"),
    State("user-session", "data"),
    State("blackjack-bet-amount", "value"),
    prevent_initial_call=True,
)
def play_blackjack(
    deal_clicks,
    hit_clicks,
    stand_clicks,
    double_clicks,
    split_clicks,
    game_state,
    user_id,
    bet_amount,
):
    """Handles the blackjack game logic with support for splitting and doubling."""
    import json

    ctx = dash.callback_context
    if not ctx.triggered:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    new_game_state = game_state.copy()
    player_hands_display = ""
    dealer_display = ""
    dealer_score_text = ""
    deal_disabled = False
    hit_disabled = True
    stand_disabled = True
    double_disabled = True
    split_disabled = True
    status_message = ""
    result_message = ""
    new_token_balance = no_update
    toast = no_update

    if button_id == "deal-button":
        if not bet_amount or bet_amount <= 0:
            toast = dbc.Toast(
                "Bet amount must be greater than 0.",
                header="Invalid Bet",
                icon="danger",
                duration=4000,
            )
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                toast,
            )

        user = get_user(user_id)
        if user["tokens"] < bet_amount:
            toast = dbc.Toast(
                "Not enough tokens for this bet.",
                header="Insufficient Funds",
                icon="warning",
                duration=4000,
            )
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                toast,
            )

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "UPDATE users SET tokens = tokens - %s WHERE id = %s RETURNING tokens;",
                (bet_amount, user_id),
            )
            new_token_balance = cur.fetchone()["tokens"]

            cur.execute(
                "INSERT INTO blackjack_rounds (user_id, initial_bet_amount, dealer_hand, dealer_score, round_status) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (user_id, bet_amount, "[]", 0, "active"),
            )
            round_id = cur.fetchone()["id"]
            conn.commit()

        deck = create_deck()
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        hand_score = calculate_hand_value(player_hand)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "INSERT INTO blackjack_hands (round_id, hand_number, bet_amount, cards, hand_score, hand_status) VALUES (%s, %s, %s, %s, %s, %s);",
                (
                    round_id,
                    1,
                    bet_amount,
                    json.dumps(player_hand),
                    hand_score,
                    "active",
                ),
            )
            conn.commit()

        new_game_state = {
            "deck": deck,
            "dealer_hand": dealer_hand,
            "hands": [
                {
                    "cards": player_hand,
                    "bet_amount": bet_amount,
                    "status": "active",
                    "is_doubled": False,
                }
            ],
            "current_hand": 0,
            "round_id": round_id,
            "game_active": True,
            "dealer_turn": False,
            "initial_bet": bet_amount,
        }

        player_score = calculate_hand_value(player_hand)
        dealer_score = calculate_hand_value(dealer_hand)

        dealer_display = f"{format_card(dealer_hand[0])} ??"
        dealer_score_text = f"Score: {calculate_hand_value([dealer_hand[0]])}"

        if player_score == 21:
            dealer_display = format_hand(dealer_hand)
            dealer_score_text = f"Score: {dealer_score}"

            if dealer_score == 21:
                result_message = "Push! Both have blackjack."
                payout = bet_amount
                game_result = "push"
            else:
                result_message = "BLACKJACK! You win!"
                payout = int(bet_amount * 2.5)
                game_result = "blackjack"

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
                    (payout, user_id),
                )
                new_token_balance = cur.fetchone()["tokens"]

                cur.execute(
                    "UPDATE blackjack_rounds SET dealer_hand = %s, dealer_score = %s, round_status = 'completed', total_payout = %s, completed_at = CURRENT_TIMESTAMP WHERE id = %s;",
                    (json.dumps(dealer_hand), dealer_score, payout, round_id),
                )

                cur.execute(
                    "UPDATE blackjack_hands SET hand_status = %s, hand_result = %s, payout_amount = %s WHERE round_id = %s AND hand_number = 1;",
                    ("blackjack", game_result, payout, round_id),
                )

                cur.execute(
                    "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
                    (
                        user_id,
                        f"blackjack_{game_result}",
                        payout - bet_amount,
                        result_message,
                    ),
                )
                conn.commit()

            new_game_state["game_active"] = False
            deal_disabled = False
        else:
            deal_disabled = True
            hit_disabled = False
            stand_disabled = False

            current_hand = new_game_state["hands"][0]
            if can_split_hand(current_hand["cards"]) and user["tokens"] >= bet_amount:
                split_disabled = False
            if can_double_down(current_hand["cards"]) and user["tokens"] >= bet_amount:
                double_disabled = False

            status_message = "Your turn - choose an action"

    elif button_id in ["hit-button", "double-button"] and game_state.get("game_active"):
        current_hand_idx = game_state["current_hand"]
        current_hand = game_state["hands"][current_hand_idx].copy()
        deck = game_state["deck"]

        is_double = button_id == "double-button"

        if is_double:
            user = get_user(user_id)
            if user["tokens"] < current_hand["bet_amount"]:
                toast = dbc.Toast(
                    "Not enough tokens to double down.",
                    header="Insufficient Funds",
                    icon="warning",
                    duration=4000,
                )
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    toast,
                )

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "UPDATE users SET tokens = tokens - %s WHERE id = %s RETURNING tokens;",
                    (current_hand["bet_amount"], user_id),
                )
                new_token_balance = cur.fetchone()["tokens"]
                conn.commit()

            current_hand["bet_amount"] *= 2
            current_hand["is_doubled"] = True

        current_hand["cards"].append(deck.pop())
        hand_score = calculate_hand_value(current_hand["cards"])

        if hand_score > 21:
            current_hand["status"] = "bust"
        elif is_double:
            current_hand["status"] = "stand"

        new_game_state = game_state.copy()
        new_game_state["deck"] = deck
        new_game_state["hands"][current_hand_idx] = current_hand

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "UPDATE blackjack_hands SET cards = %s, hand_score = %s, hand_status = %s, bet_amount = %s, is_doubled = %s WHERE round_id = %s AND hand_number = %s;",
                (
                    json.dumps(current_hand["cards"]),
                    hand_score,
                    current_hand["status"],
                    current_hand["bet_amount"],
                    current_hand["is_doubled"],
                    game_state["round_id"],
                    current_hand_idx + 1,
                ),
            )
            conn.commit()

        if current_hand["status"] in ["bust", "stand"]:
            next_hand_idx = current_hand_idx + 1
            if next_hand_idx < len(new_game_state["hands"]):
                new_game_state["current_hand"] = next_hand_idx
                next_hand = new_game_state["hands"][next_hand_idx]
                if next_hand["status"] == "active":
                    hit_disabled = False
                    stand_disabled = False
                    if can_double_down(next_hand["cards"]):
                        user = get_user(user_id)
                        if user["tokens"] >= next_hand["bet_amount"]:
                            double_disabled = False
                    status_message = f"Playing hand {next_hand_idx + 1}"
            else:
                new_game_state["dealer_turn"] = True
                status_message = "Dealer's turn"
        else:
            hit_disabled = False
            stand_disabled = False
            double_disabled = True
            split_disabled = True
            status_message = f"Playing hand {current_hand_idx + 1}"

        dealer_display = f"{format_card(game_state['dealer_hand'][0])} ??"
        dealer_score_text = (
            f"Score: {calculate_hand_value([game_state['dealer_hand'][0]])}"
        )

    elif button_id == "split-button" and game_state.get("game_active"):
        current_hand_idx = game_state["current_hand"]
        current_hand = game_state["hands"][current_hand_idx].copy()

        user = get_user(user_id)
        if user["tokens"] < current_hand["bet_amount"]:
            toast = dbc.Toast(
                "Not enough tokens to split.",
                header="Insufficient Funds",
                icon="warning",
                duration=4000,
            )
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                toast,
            )

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "UPDATE users SET tokens = tokens - %s WHERE id = %s RETURNING tokens;",
                (current_hand["bet_amount"], user_id),
            )
            new_token_balance = cur.fetchone()["tokens"]
            conn.commit()

        deck = game_state["deck"]

        first_card = current_hand["cards"][0]
        second_card = current_hand["cards"][1]

        current_hand["cards"] = [first_card, deck.pop()]
        current_hand["status"] = "active"

        second_hand = {
            "cards": [second_card, deck.pop()],
            "bet_amount": current_hand["bet_amount"],
            "status": "active",
            "is_doubled": False,
        }

        new_game_state = game_state.copy()
        new_game_state["deck"] = deck
        new_game_state["hands"][current_hand_idx] = current_hand
        new_game_state["hands"].append(second_hand)

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            hand_score = calculate_hand_value(current_hand["cards"])
            cur.execute(
                "UPDATE blackjack_hands SET cards = %s, hand_score = %s WHERE round_id = %s AND hand_number = %s;",
                (
                    json.dumps(current_hand["cards"]),
                    hand_score,
                    game_state["round_id"],
                    current_hand_idx + 1,
                ),
            )

            hand_score = calculate_hand_value(second_hand["cards"])
            cur.execute(
                "INSERT INTO blackjack_hands (round_id, hand_number, bet_amount, cards, hand_score, hand_status) VALUES (%s, %s, %s, %s, %s, %s);",
                (
                    game_state["round_id"],
                    len(new_game_state["hands"]),
                    second_hand["bet_amount"],
                    json.dumps(second_hand["cards"]),
                    hand_score,
                    "active",
                ),
            )
            conn.commit()

        hit_disabled = False
        stand_disabled = False
        if can_double_down(current_hand["cards"]):
            user = get_user(user_id)
            if user["tokens"] >= current_hand["bet_amount"]:
                double_disabled = False
        split_disabled = True
        status_message = f"Playing hand 1 of {len(new_game_state['hands'])}"

        dealer_display = f"{format_card(game_state['dealer_hand'][0])} ??"
        dealer_score_text = (
            f"Score: {calculate_hand_value([game_state['dealer_hand'][0]])}"
        )

    elif button_id == "stand-button" and game_state.get("game_active"):
        current_hand_idx = game_state["current_hand"]
        current_hand = game_state["hands"][current_hand_idx].copy()
        current_hand["status"] = "stand"

        new_game_state = game_state.copy()
        new_game_state["hands"][current_hand_idx] = current_hand

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "UPDATE blackjack_hands SET hand_status = 'stand' WHERE round_id = %s AND hand_number = %s;",
                (game_state["round_id"], current_hand_idx + 1),
            )
            conn.commit()

        next_hand_idx = current_hand_idx + 1
        if next_hand_idx < len(new_game_state["hands"]):
            new_game_state["current_hand"] = next_hand_idx
            next_hand = new_game_state["hands"][next_hand_idx]
            if next_hand["status"] == "active":
                hit_disabled = False
                stand_disabled = False
                if can_double_down(next_hand["cards"]):
                    user = get_user(user_id)
                    if user["tokens"] >= next_hand["bet_amount"]:
                        double_disabled = False
                status_message = f"Playing hand {next_hand_idx + 1}"
        else:
            new_game_state["dealer_turn"] = True
            status_message = "Dealer's turn"

        dealer_display = f"{format_card(game_state['dealer_hand'][0])} ??"
        dealer_score_text = (
            f"Score: {calculate_hand_value([game_state['dealer_hand'][0]])}"
        )

    if new_game_state.get("dealer_turn") and new_game_state.get("game_active"):
        dealer_hand = new_game_state["dealer_hand"].copy()
        deck = new_game_state["deck"]
        dealer_score = calculate_hand_value(dealer_hand)

        while dealer_score < 17:
            dealer_hand.append(deck.pop())
            dealer_score = calculate_hand_value(dealer_hand)

        new_game_state["dealer_hand"] = dealer_hand

        total_payout = 0
        results = []

        for i, hand in enumerate(new_game_state["hands"]):
            hand_score = calculate_hand_value(hand["cards"])

            if hand["status"] == "bust":
                result = "lose"
                payout = 0
            elif dealer_score > 21:
                result = "win"
                payout = hand["bet_amount"] * 2
            elif hand_score > dealer_score:
                result = "win"
                payout = hand["bet_amount"] * 2
            elif dealer_score > hand_score:
                result = "lose"
                payout = 0
            else:
                result = "push"
                payout = hand["bet_amount"]

            total_payout += payout
            results.append(f"Hand {i+1}: {result.title()} (${payout})")

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "UPDATE blackjack_hands SET hand_result = %s, payout_amount = %s WHERE round_id = %s AND hand_number = %s;",
                    (result, payout, new_game_state["round_id"], i + 1),
                )

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
                (total_payout, user_id),
            )
            new_token_balance = cur.fetchone()["tokens"]

            cur.execute(
                "UPDATE blackjack_rounds SET dealer_hand = %s, dealer_score = %s, round_status = 'completed', total_payout = %s, completed_at = CURRENT_TIMESTAMP WHERE id = %s;",
                (
                    json.dumps(dealer_hand),
                    dealer_score,
                    total_payout,
                    new_game_state["round_id"],
                ),
            )

            net_change = total_payout - sum(
                hand["bet_amount"] for hand in new_game_state["hands"]
            )
            cur.execute(
                "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
                (
                    user_id,
                    "blackjack_round",
                    net_change,
                    f"Blackjack round completed: {'; '.join(results)}",
                ),
            )
            conn.commit()

        new_game_state["game_active"] = False
        deal_disabled = False
        hit_disabled = True
        stand_disabled = True
        double_disabled = True
        split_disabled = True

        dealer_display = format_hand(dealer_hand)
        dealer_score_text = f"Score: {dealer_score}"
        result_message = f"Round Complete! Total payout: {total_payout} tokens"
        status_message = "; ".join(results)

    if new_game_state.get("hands"):
        hands_components = []
        for i, hand in enumerate(new_game_state["hands"]):
            is_current = i == new_game_state.get("current_hand", 0)
            hand_score = calculate_hand_value(hand["cards"])

            border_class = (
                "border-warning border-3"
                if is_current and new_game_state.get("game_active")
                else "border"
            )

            hand_component = dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6(
                                f"Hand {i+1} {'(Current)' if is_current and new_game_state.get('game_active') else ''} - Bet: {hand['bet_amount']} {'(Doubled)' if hand.get('is_doubled') else ''}",
                                className="text-center mb-2",
                            ),
                            html.Div(
                                format_hand(hand["cards"]),
                                className=f"fs-5 text-center p-2 rounded bg-light text-dark {border_class}",
                            ),
                            html.Div(
                                f"Score: {hand_score} ({hand['status'].title()})",
                                className="text-center fw-bold mt-1",
                            ),
                        ],
                        width=12,
                    )
                ],
                className="mb-3",
            )

            hands_components.append(hand_component)

        player_hands_display = html.Div(hands_components)

    return (
        new_game_state,
        player_hands_display,
        dealer_display,
        dealer_score_text,
        deal_disabled,
        hit_disabled,
        stand_disabled,
        double_disabled,
        split_disabled,
        status_message,
        result_message,
        new_token_balance,
        toast,
    )


# --- Food Station Tab ---
def render_food_tab(user_id):
    """Renders the layout for the food station."""
    menu_items = get_food_menu()
    menu_table = dbc.Table(
        # Header
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Item"),
                        html.Th("Description"),
                        html.Th("Price (Tokens)"),
                        html.Th("Action"),
                    ]
                )
            )
        ]
        +
        # Body
        [
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(item["name"]),
                            html.Td(item["description"]),
                            html.Td(item["price"]),
                            html.Td(
                                dbc.Button(
                                    "Buy",
                                    id={"type": "buy-food-btn", "item_id": item["id"]},
                                    color="info",
                                    size="sm",
                                )
                            ),
                        ]
                    )
                    for item in menu_items
                ]
            )
        ],
        bordered=True,
        striped=True,
        hover=True,
        responsive=True,
    )
    return dbc.Card(
        dbc.CardBody(
            [
                dcc.Store(id="card-select-dropdown", storage_type="local"),
                html.H4("Food & Refreshments", className="card-title text-center"),
                html.P(
                    "Use your winnings to buy a tasty treat!",
                    className="text-center mb-4",
                ),
                menu_table,
            ]
        )
    )


@app.callback(
    Output("user-tokens-display", "children", allow_duplicate=True),
    Output("notification-toast-container", "children", allow_duplicate=True),
    Input({"type": "buy-food-btn", "item_id": dash.ALL}, "n_clicks"),
    State("user-session", "data"),
    prevent_initial_call=True,
)
def buy_food(n_clicks, user_id):
    """Handles the logic for purchasing a food item."""
    ctx = dash.callback_context

    if not ctx.triggered or not any(click for click in n_clicks if click is not None):
        return no_update, no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    item_id = eval(button_id)["item_id"]

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get item price and user tokens
        cur.execute("SELECT price, name FROM food_menu WHERE id = %s;", (item_id,))
        item = cur.fetchone()
        cur.execute("SELECT tokens FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()

        if not item or not user:
            toast = dbc.Toast(
                "An error occurred.", header="Error", icon="danger", duration=4000
            )
            return no_update, toast

        if user["tokens"] < item["price"]:
            toast = dbc.Toast(
                f"Not enough tokens to buy {item['name']}.",
                header="Insufficient Funds",
                icon="warning",
                duration=4000,
            )
            return no_update, toast

        # Perform transaction
        token_change = -item["price"]
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (token_change, user_id),
        )
        new_balance = cur.fetchone()["tokens"]
        # Log food purchase
        cur.execute(
            "INSERT INTO food_purchases (user_id, food_item_id, quantity, total_price) VALUES (%s, %s, 1, %s);",
            (user_id, item_id, item["price"]),
        )
        # Log generic transaction
        cur.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
            (user_id, "food_purchase", token_change, f"Purchased {item['name']}."),
        )
        conn.commit()

    toast = dbc.Toast(
        f"You purchased a {item['name']}! Enjoy!",
        header="Order Up!",
        icon="success",
        duration=4000,
    )
    return new_balance, toast


# Transaction History
def render_history_tab(user_id):
    return dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Button(
                            "View Action History",
                            id="toggle-history",
                            color="secondary",
                            className="w-100",
                        )
                    ),
                    dbc.Collapse(
                        dbc.CardBody(html.Div(id="history-log")),
                        id="history-collapse",
                        is_open=False,
                    ),
                ]
            )
        ]
    )


@app.callback(
    Output("history-collapse", "is_open"),
    Input("toggle-history", "n_clicks"),
    State("history-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_history(n, is_open):
    return not is_open


@app.callback(
    Output("history-log", "children"),
    Input("history-collapse", "is_open"),
    State("user-session", "data"),
    prevent_initial_call=True,
)
def load_history(is_open, user_id):
    if not is_open:
        return no_update

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT transaction_type, amount, description, created_at
            FROM transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20;
        """,
            (user_id,),
        )
        logs = cur.fetchall()

    if not logs:
        return html.P("No transactions yet.")

    return dbc.ListGroup(
        [
            dbc.ListGroupItem(
                [
                    html.Strong(
                        f"{log['transaction_type'].replace('_', ' ').title()}: "
                    ),
                    f"{log['description']} ({log['amount']} tokens) – ",
                    html.Span(
                        log["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                        className="text-muted",
                    ),
                ]
            )
            for log in logs
        ]
    )


# --- Main Execution ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
