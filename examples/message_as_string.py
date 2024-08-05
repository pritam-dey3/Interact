from interact.base import Message


def main():
    msg = Message("You are a wizard", sender="Harry Potter")

    # use common string methods
    msg2 = msg + " Harmoine Granger"
    msg3 = msg2.replace("Harmoine", "Hermione")
    msg4 = msg3.upper()
    msg5 = msg4[:10]

    print(msg2, msg3, msg4, msg5, sep="\n")


if __name__ == "__main__":
    main()



