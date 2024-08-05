from interact.base import Message

msg = Message("You are a wizard", sender="Harry Potter")

# use common string methods
msg2 = msg + " Harmoine Granger"
msg3 = msg2.replace("Harmoine", "Hermione")
msg4 = msg3.upper()
msg5 = msg4[:10]



