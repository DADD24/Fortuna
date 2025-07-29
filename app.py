# app.py
# This is the main application file.
# It contains the Dash layout and all the business logic for the casino.

import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import psycopg2
import psycopg2.extras
import random
import os
import time

# --- Database Configuration ---
# It's good practice to retry the connection to give the DB container time to start.
time.sleep(5) # A simple delay to wait for the DB to initialize.
try:
    conn = psycopg2.connect(
        dbname="casino_db",
        user="casino_user",
        password="casino_password",
        host="localhost", # Use 'db' if running this app in a docker container in the same network
        port="5432"
    )
except psycopg2.OperationalError as e:
    print(f"Could not connect to database: {e}")
    # In a real app, you'd have more robust retry logic.
    exit()

# --- Dash App Initialization ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
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
        cur.execute("SELECT * FROM users WHERE email = %s AND username = %s;", (email, username))
        return cur.fetchone()

def create_user(email, username):
    """Creates a new user and returns their data."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "INSERT INTO users (email, username) VALUES (%s, %s) RETURNING *;",
            (email, username)
        )
        conn.commit()
        return cur.fetchone()

def get_user_cards(user_id):
    """Fetches all credit cards for a given user."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id, card_number FROM credit_cards WHERE user_id = %s;", (user_id,))
        return cur.fetchall()

def get_food_menu():
    """Fetches the entire food menu."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM food_menu ORDER BY price;")
        return cur.fetchall()

# --- App Layout ---
app.layout = html.Div([
    # Store for user session data (user_id)
    dcc.Store(id='user-session', storage_type='local'),

    # Header
    html.Div(
        className="text-center p-4 bg-primary text-white",
        children=[
            html.H1("Welcome to the Dash Casino"),
            html.P("A demonstration of SQL databases and business logic.")
        ]
    ),

    # Main content area with tabs
    dbc.Container(
        id='main-content',
        className="mt-4",
        fluid=True,
        children=[
            # Placeholder for content, will be updated by callbacks
        ]
    ),

    # Notification area
    html.Div(id='notification-toast-container', style={'position': 'fixed', 'top': 66, 'right': 10, 'zIndex': 1050})
])

# --- Content Layouts ---

def create_login_layout():
    """Returns the layout for the login screen."""
    return dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H4("User Login / Sign Up")),
                dbc.CardBody([
                    dbc.Input(id='login-email', placeholder='Enter your email...', type='email', className='mb-3'),
                    dbc.Input(id='login-username', placeholder='Enter your username...', type='text', className='mb-3'),
                    dbc.Button("Login / Register", id='login-button', color='success', className='w-100')
                ])
            ]),
            width={'size': 6, 'offset': 3}
        ),
        className="mt-5"
    )

def create_main_layout(user_data):
    """Returns the main application layout after login."""
    return html.Div([
        dbc.Row([
            dbc.Col(html.H3(f"Welcome, {user_data['username']}!"), width=8),
            dbc.Col(
                html.Div([
                    html.Strong("Tokens: "),
                    html.Span(user_data['tokens'], id='user-tokens-display')
                ]),
                width=3,
                className="text-end fs-4"
            ),
            dbc.Col(dbc.Button("Logout", id="logout-button", color="danger", size="sm"), width=1)
        ]),
        html.Hr(),
        dbc.Tabs(
            id="app-tabs",
            active_tab="tab-slots",
            children=[
                dbc.Tab(label="Slots", tab_id="tab-slots"),
                dbc.Tab(label="Wallet", tab_id="tab-wallet"),
                dbc.Tab(label="Food Station", tab_id="tab-food"),
            ],
        ),
        html.Div(id="tab-content", className="p-4")
    ])

# --- Callbacks ---

@app.callback(
    Output('main-content', 'children'),
    Input('user-session', 'data')
)
def render_main_content(user_id):
    """Renders the main content based on whether the user is logged in."""
    if user_id:
        user_data = get_user(user_id)
        if user_data:
            return create_main_layout(user_data)
    return create_login_layout()

@app.callback(
    Output('user-session', 'data', allow_duplicate=True),
    Output('notification-toast-container', 'children', allow_duplicate=True),
    Input('login-button', 'n_clicks'),
    State('login-email', 'value'),
    State('login-username', 'value'),
    prevent_initial_call=True
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

    toast = dbc.Toast(toast_message, header=toast_header, icon=toast_icon, duration=4000)
    return user['id'], toast

@app.callback(
    Output('user-session', 'data'),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """Logs the user out by clearing the session data."""
    if n_clicks is None:
        return no_update
    return None # Setting data to None effectively logs them out

@app.callback(
    Output("tab-content", "children"),
    Input("app-tabs", "active_tab"),
    State("user-session", "data")
)
def render_tab_content(active_tab, user_id):
    """Renders the content for the selected tab."""
    if not user_id:
        return "Please log in to see content."
    if active_tab == "tab-wallet":
        return render_wallet_tab(user_id)
    elif active_tab == "tab-slots":
        return render_slots_tab(user_id)
    elif active_tab == "tab-food":
        return render_food_tab(user_id)
    return html.P("This is the content of the selected tab.")

# --- Wallet Tab ---
def render_wallet_tab(user_id):
    cards = get_user_cards(user_id)
    card_list = [dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}") for card in cards] if cards else [dbc.ListGroupItem("No cards on file.")]

    return html.Div([
        dbc.Row([
            # Add Credit Card
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Add a New Credit Card"),
                    dbc.CardBody([
                        dbc.Input(id='new-card-number', placeholder='Enter 16-digit card number', type='text', maxLength=16, minLength=16),
                        dbc.Button("Add Card", id='add-card-button', color='primary', className='mt-3 w-100')
                    ])
                ]),
                md=6
            ),
            # View Cards
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Your Credit Cards"),
                    dbc.CardBody(dbc.ListGroup(card_list, id='card-list-group'))
                ]),
                md=6
            )
        ]),
        html.Hr(className="my-4"),
        # Purchase Tokens
        dbc.Card([
            dbc.CardHeader("Purchase Tokens"),
            dbc.CardBody([
                html.P("Select a credit card and an amount to purchase."),
                dbc.Select(
                    id='card-select-dropdown',
                    options=[{'label': f"Card ending in {c['card_number'][-4:]}", 'value': c['id']} for c in cards],
                    placeholder="Select a card..."
                ),
                html.Div(
                    className="d-grid gap-2 d-md-flex justify-content-md-start mt-3",
                    children=[
                        dbc.Button("Buy 100 Tokens", id={'type': 'buy-tokens-btn', 'amount': 100}, color='success'),
                        dbc.Button("Buy 500 Tokens", id={'type': 'buy-tokens-btn', 'amount': 500}, color='success'),
                        dbc.Button("Buy 1000 Tokens", id={'type': 'buy-tokens-btn', 'amount': 1000}, color='success'),
                    ]
                )
            ])
        ])
    ])

@app.callback(
    Output('card-list-group', 'children'),
    Output('card-select-dropdown', 'options'),
    Output('notification-toast-container', 'children', allow_duplicate=True),
    Input('add-card-button', 'n_clicks'),
    State('user-session', 'data'),
    State('new-card-number', 'value'),
    prevent_initial_call=True
)
def add_credit_card(n_clicks, user_id, card_number):
    """Adds a new credit card for the user."""
    if not card_number:
        cards = get_user_cards(user_id)
        card_list = [dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}") for card in cards]
        card_options = [{'label': f"Card ending in {c['card_number'][-4:]}", 'value': c['id']} for c in cards]

        return card_list, card_options, no_update

    if not card_number.isdigit() or len(card_number) != 16:
        toast = dbc.Toast("Please enter a valid 16-digit card number.", header="Error", icon="danger", duration=4000)
        return no_update, no_update, toast

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO credit_cards (user_id, card_number) VALUES (%s, %s);",
            (user_id, card_number)
        )
        conn.commit()

    cards = get_user_cards(user_id)
    card_list = [dbc.ListGroupItem(f"**** **** **** {card['card_number'][-4:]}") for card in cards]
    card_options = [{'label': f"Card ending in {c['card_number'][-4:]}", 'value': c['id']} for c in cards]
    toast = dbc.Toast("Credit card added successfully!", header="Success", icon="success", duration=4000)

    return card_list, card_options, toast

@app.callback(
    Output('user-tokens-display', 'children', allow_duplicate=True),
    Output('notification-toast-container', 'children', allow_duplicate=True),
    Input({'type': 'buy-tokens-btn', 'amount': dash.ALL}, 'n_clicks'),
    State('user-session', 'data'),
    State('card-select-dropdown', 'value'),
    prevent_initial_call=True
)
def buy_tokens(n_clicks, user_id, card_id):
    """Handles token purchase logic."""
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return no_update, no_update

    if not card_id:
        toast = dbc.Toast("Please add a credit card first.", header="Error", icon="warning", duration=4000)
        return no_update, toast

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    amount_to_buy = eval(button_id)['amount']

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Add tokens to user
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (amount_to_buy, user_id)
        )
        new_balance = cur.fetchone()['tokens']
        # Log transaction
        cur.execute(
            "INSERT INTO transactions (user_id, card_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s, %s);",
            (user_id, card_id, 'purchase_tokens', amount_to_buy, f"Purchased {amount_to_buy} tokens.")
        )
        conn.commit()

    toast = dbc.Toast(f"Successfully purchased {amount_to_buy} tokens!", header="Purchase Complete", icon="success", duration=4000)
    return new_balance, toast


# --- Slots Tab ---
def render_slots_tab(user_id):
    """Renders the layout for the slots game."""
    return dbc.Card(
        dbc.CardBody([
            dcc.Store(id='card-select-dropdown', storage_type='local'),
            html.H4("Slot Machine", className="card-title text-center"),
            html.P("Place your bet and pull the lever!", className="text-center"),
            # Reels Display
            dbc.Row(
                [
                    dbc.Col(html.Div("?", id='reel-1', className="fs-1 text-center p-4 border rounded bg-light text-dark"), width=4),
                    dbc.Col(html.Div("?", id='reel-2', className="fs-1 text-center p-4 border rounded bg-light text-dark"), width=4),
                    dbc.Col(html.Div("?", id='reel-3', className="fs-1 text-center p-4 border rounded bg-light text-dark"), width=4),
                ],
                className="mb-4"
            ),
            # Bet Amount
            dbc.InputGroup(
                [
                    dbc.InputGroupText("Bet Amount"),
                    dbc.Input(id='bet-amount', type='number', value=10, min=1, step=1),
                ],
                className="mb-3"
            ),
            # Spin Button
            dbc.Button("Spin!", id='spin-button', color='warning', size='lg', className='w-100'),
            # Result Message
            html.Div(id='spin-result-message', className="mt-3 text-center fs-4 fw-bold")
        ])
    )

@app.callback(
    Output('reel-1', 'children'),
    Output('reel-2', 'children'),
    Output('reel-3', 'children'),
    Output('spin-result-message', 'children'),
    Output('user-tokens-display', 'children'),
    Output('notification-toast-container', 'children', allow_duplicate=True),
    Input('spin-button', 'n_clicks'),
    State('user-session', 'data'),
    State('bet-amount', 'value'),
    prevent_initial_call=True
)
def play_slots(n_clicks, user_id, bet_amount):
    """Handles the logic for a single spin of the slot machine."""
    if n_clicks is None:
        return no_update, no_update, no_update, no_update, no_update, no_update
    
    if not bet_amount or bet_amount <= 0:
        toast = dbc.Toast("Bet amount must be greater than 0.", header="Invalid Bet", icon="danger", duration=4000)
        return no_update, no_update, no_update, no_update, no_update, toast

    user = get_user(user_id)
    if user['tokens'] < bet_amount:
        toast = dbc.Toast("Not enough tokens for this bet.", header="Insufficient Funds", icon="warning", duration=4000)
        return no_update, no_update, no_update, no_update, no_update, toast

    # --- Game Logic ---
    symbols = ['🍒', '🍋', '🍊', '🔔', 'BAR', '7️⃣']
    weights = [0.3, 0.25, 0.2, 0.15, 0.08, 0.02] # Cherry is most common, 7 is rarest
    payouts = {'🍒': 2, '🍋': 3, '🍊': 5, '🔔': 10, 'BAR': 25, '7️⃣': 100}

    reels = [random.choices(symbols, weights=weights, k=1)[0] for _ in range(3)]
    is_win = (reels[0] == reels[1] == reels[2])
    payout_amount = 0
    token_change = -bet_amount
    result_message = ""

    if is_win:
        winning_symbol = reels[0]
        payout_multiplier = payouts[winning_symbol]
        payout_amount = bet_amount * payout_multiplier
        token_change += payout_amount
        result_message = f"JACKPOT! You won {payout_amount} tokens!"
        result_style = {'color': 'gold'}
    else:
        result_message = "Better luck next time!"
        result_style = {'color': 'white'}

    # --- Database Update ---
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Update user tokens
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (token_change, user_id)
        )
        new_balance = cur.fetchone()['tokens']
        # Log the spin
        cur.execute(
            "INSERT INTO slots_spins (user_id, bet_amount, reels, is_win, payout_amount) VALUES (%s, %s, %s, %s, %s);",
            (user_id, bet_amount, '-'.join(reels), is_win, payout_amount)
        )
        conn.commit()

    return reels[0], reels[1], reels[2], html.Span(result_message, style=result_style), new_balance, no_update


# --- Food Station Tab ---
def render_food_tab(user_id):
    """Renders the layout for the food station."""
    menu_items = get_food_menu()
    menu_table = dbc.Table(
        # Header
        [html.Thead(html.Tr([html.Th("Item"), html.Th("Description"), html.Th("Price (Tokens)"), html.Th("Action")]))] +
        # Body
        [html.Tbody([
            html.Tr([
                html.Td(item['name']),
                html.Td(item['description']),
                html.Td(item['price']),
                html.Td(dbc.Button("Buy", id={'type': 'buy-food-btn', 'item_id': item['id']}, color='info', size='sm'))
            ]) for item in menu_items
        ])],
        bordered=True,
        striped=True,
        hover=True,
        responsive=True,
    )
    return dbc.Card(
        dbc.CardBody([
            dcc.Store(id='card-select-dropdown', storage_type='local'),
            html.H4("Food & Refreshments", className="card-title text-center"),
            html.P("Use your winnings to buy a tasty treat!", className="text-center mb-4"),
            menu_table
        ])
    )

@app.callback(
    Output('user-tokens-display', 'children', allow_duplicate=True),
    Output('notification-toast-container', 'children', allow_duplicate=True),
    Input({'type': 'buy-food-btn', 'item_id': dash.ALL}, 'n_clicks'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def buy_food(n_clicks, user_id):
    """Handles the logic for purchasing a food item."""
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    item_id = eval(button_id)['item_id']

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get item price and user tokens
        cur.execute("SELECT price, name FROM food_menu WHERE id = %s;", (item_id,))
        item = cur.fetchone()
        cur.execute("SELECT tokens FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()

        if not item or not user:
            toast = dbc.Toast("An error occurred.", header="Error", icon="danger", duration=4000)
            return no_update, toast

        if user['tokens'] < item['price']:
            toast = dbc.Toast(f"Not enough tokens to buy {item['name']}.", header="Insufficient Funds", icon="warning", duration=4000)
            return no_update, toast

        # Perform transaction
        token_change = -item['price']
        cur.execute(
            "UPDATE users SET tokens = tokens + %s WHERE id = %s RETURNING tokens;",
            (token_change, user_id)
        )
        new_balance = cur.fetchone()['tokens']
        # Log food purchase
        cur.execute(
            "INSERT INTO food_purchases (user_id, food_item_id, quantity, total_price) VALUES (%s, %s, 1, %s);",
            (user_id, item_id, item['price'])
        )
        # Log generic transaction
        cur.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s);",
            (user_id, 'food_purchase', token_change, f"Purchased {item['name']}.")
        )
        conn.commit()

    toast = dbc.Toast(f"You purchased a {item['name']}! Enjoy!", header="Order Up!", icon="success", duration=4000)
    return new_balance, toast


# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
