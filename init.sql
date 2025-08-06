CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    tokens INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the credit_cards table.
-- This table stores credit card information linked to a user.
-- The user_id is a foreign key referencing the users table.
CREATE TABLE credit_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_number VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create the transactions table to log token purchases.
-- This provides an audit trail for all financial activities.
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_id INTEGER,
    transaction_type VARCHAR(50) NOT NULL, -- e.g., 'purchase_tokens', 'slot_win', 'food_purchase', 'convert_to_cash'
    amount INTEGER NOT NULL, -- Can be positive (win) or negative (purchase)
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES credit_cards (id) ON DELETE SET NULL
);

-- Create the slots_spins table to log each game played.
-- This is useful for analytics and game balancing.
CREATE TABLE slots_spins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bet_amount INTEGER NOT NULL,
    reels VARCHAR(50) NOT NULL, -- e.g., 'CHERRY-BAR-LEMON'
    is_win BOOLEAN NOT NULL,
    payout_amount INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create the food_menu table to store available food items.
CREATE TABLE food_menu (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL
);

-- Create the food_purchases table to log food orders.
CREATE TABLE food_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    food_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_price INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_menu (id)
);

-- Create the blackjack_games table to log each blackjack game played.
CREATE TABLE blackjack_games (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bet_amount INTEGER NOT NULL,
    player_hand TEXT NOT NULL, -- JSON string of player's cards
    dealer_hand TEXT NOT NULL, -- JSON string of dealer's cards
    player_score INTEGER NOT NULL,
    dealer_score INTEGER NOT NULL,
    game_result VARCHAR(20) NOT NULL, -- 'win', 'lose', 'push', 'blackjack'
    payout_amount INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Insert some default items into the food menu for demonstration.
INSERT INTO food_menu (name, description, price) VALUES
('Casino Burger', 'A juicy all-beef patty with our special sauce.', 15),
('High Roller Hot Dog', 'A classic dog with all the fixings.', 10),
('Jackpot Fries', 'Crispy fries smothered in cheese and bacon.', 8),
('Winner Winner Chicken Dinner', 'A full roasted chicken, serves two.', 50),
('Lucky Lemonade', 'Freshly squeezed and very lucky.', 5);
