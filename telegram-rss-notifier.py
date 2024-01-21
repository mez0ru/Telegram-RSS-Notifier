import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import sqlite3
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# INIT
con = sqlite3.connect("data.db")
cur = con.cursor()
with open('init.sql', 'r') as content_file:
  cur.executescript(content_file.read())
  con.commit()

# Load startup options
with open('startup.json', 'r') as f:
  startup_options = json.load(f)
    
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if len(context.args) == 2:
    cur.execute("INSERT INTO rss(name, link, etag) VALUES (?, ?, NULL);", [context.args[0], context.args[1]])
    con.commit()
    await update.message.reply_text(f'Successfully added {context.args[0]}')
  else:
    await update.message.reply_text("""
Wrong command, make sure you provide *BOTH* the _name_ and the _feed link_.
Example:
/add My-feed https://example.com/feed.xml""", parse_mode=ParseMode.MARKDOWN)

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if len(context.args) == 1:
    # Check if query is about removing a check condition
    if ';' in context.args[0]:
      [url, content] = context.args[0].split(';', 1)
      cur.execute("""
        DELETE FROM contentCondition
        WHERE id IN (
          SELECT cc.id FROM contentCondition cc
          INNER JOIN urlCondition uc
          ON uc.id=cc.url_condition_id
          WHERE url=? and content=?
        );
      """, [url, content])
      await update.message.reply_text(f'Successfully removed a condition where _url_ "{url}" _has_ "{content}"', parse_mode=ParseMode.MARKDOWN)
    else:
      cur.execute("DELETE FROM rss WHERE name = ?;", [context.args[0]])
      con.commit()
      await update.message.reply_text(f'Successfully removed {context.args[0]}')
  else:
    await update.message.reply_text("No name provided or a condition, *nothing* is _done_.", parse_mode=ParseMode.MARKDOWN)

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  data = urlopen('https://www.reddit.com/r/funny/new/.rss')
  root = ET.fromstring(data.read())
  # await update.message.reply_text(f'Hello {update.effective_user.first_name}')
  first_entry = root.find("default:entry", startup_options['namespaces'])
  await update.message.reply_text(f'Title: {first_entry.find("default:title", startup_options["namespaces"]).text}\n{first_entry.find("default:link", startup_options["namespaces"]).attrib["href"]}')

async def repeat(context: ContextTypes.DEFAULT_TYPE) -> None:
  await context.bot.send_message(context.job.chat_id, 'repeat test')


app = ApplicationBuilder().token(startup_options['token']).build()
job_queue = app.job_queue

app.add_handler(CommandHandler("test", test))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("remove", remove))

job = job_queue.run_repeating(repeat, startup_options['interval'] * 60, chat_id=startup_options['chat_id'])
job_queue.run_once(repeat, 1, chat_id=startup_options['chat_id'])

app.run_polling()

con.close()
