import openai
import telebot
import requests
import logging

# Set up OpenAI API credentials
openai.api_key = "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"

# Set up Telegram Bot API credentials
bot = telebot.TeleBot("6584365028:AAFGJU4yPCfaeacABxksW-6tZAuqN5gKi5M")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Define function to generate OpenAI response
def generate_response(input_text):
    response = ""
    try:
        prompt = "You are a Crypto A.I bot respond to user  input: "+input_text.strip()+""
        model = "text-davinci-002"
        completions = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
            presence_penalty=0.5,
            frequency_penalty=0.5,
        )
        message = completions.choices[0].text
        response = message.strip()
    except Exception as e:
        logging.error(e)
    return response

# Define function to check honeypot
def check_honeypot(contract_address, message):
    honeypot_api_endpoint = f'https://api.honeypot.is/v2/IsHoneypot?address={contract_address}'
    top_holders_api_endpoint = f'https://api.honeypot.is/v1/TopHolders?address={contract_address}&chainID=1'

    try:
        honeypot_response = requests.get(honeypot_api_endpoint)
        honeypot_json = honeypot_response.json()

        if honeypot_response.status_code == 200:
            if honeypot_json["honeypotResult"]["isHoneypot"]:
                return "❌ High Risk of Honeypot ❌\nDetected honeypot! Exercise caution."

            else:
                token_name = honeypot_json["token"]["name"]
                dex_name = honeypot_json["pair"]["pair"]["name"]
                liq_value = honeypot_json["pair"]["liquidity"]

                top_holders_response = requests.get(top_holders_api_endpoint)
                top_holders_json = top_holders_response.json()

                if top_holders_response.status_code == 200:
                    top_holders_info = get_top_holders_info(top_holders_json)

                    result_message = (
                        f"✅ Low Risk of Honeypot ✅\n"
                        f"Didn't detect any risks. Always do your own due diligence!\n\n"
                        f"🧾Token: {token_name}\n"
                        f"📊DEX: {dex_name}\n\n"
                        f"🌊LIQ: ${liq_value:,.2f}\n"
                        f"👥TOP 3 HOLDERS INFO:\n{top_holders_info}\n"
                        f"📝CONTRACT: OPEN SOURCE"
                    )

                    return result_message

                else:
                    return f"Error: {top_holders_response.status_code} - {top_holders_response.text}"

        else:
            return f"Error: {honeypot_response.status_code} - {honeypot_response.text}"

    except requests.exceptions.RequestException as e:
        return f"Request Exception: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Define function to get top holders info
def get_top_holders_info(top_holders_json):
    total_supply = int(top_holders_json["totalSupply"])
    holders = top_holders_json["holders"]
    sorted_holders = sorted(holders, key=lambda x: int(x["balance"]), reverse=True)

    top_holders_info = ""
    for index, holder in enumerate(sorted_holders[:3], start=1):
        balance = int(holder["balance"])
        percentage_of_total_supply = (balance / total_supply) * 100
        top_holders_info += (
            f"{index}. Holder: {holder['address']}\n"
            f"   Balance: {holder['balance']}\n"
            f"   Percentage of Total Supply: {percentage_of_total_supply:.2f}%\n\n"
        )

    return top_holders_info

# Define function to handle incoming Telegram messages
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hi, I am Synk. Please send me a message and I will do my best to respond.")
    logging.info(f"Received {message.text} from {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text.startswith('/ask'):
        input_text = message.text.replace('/ask', '').strip()
        response = generate_response(input_text)
        if response:
            bot.reply_to(message, response)
            logging.info(f"Received {input_text} from {message.chat.id} and sent {response}")
        else:
            bot.reply_to(message, "I'm sorry, I didn't understand that.")
            logging.info(f"Unable to generate response for {input_text} from {message.chat.id}")
    
    elif message.text.startswith('/scan'):
        contract_address = message.text.replace('/scan', '').strip()
        result_message = check_honeypot(contract_address, message)
        bot.reply_to(message, result_message)
        logging.info(f"Received {message.text} from {message.chat.id} and sent {result_message}")

    else:
        bot.reply_to(message, "I'm sorry, I didn't understand that.")
        logging.info(f"Received unknown command {message.text} from {message.chat.id}")

# Start the bot
logging.info("Starting bot...")
bot.polling(none_stop=True)
