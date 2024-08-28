class MaxLength:
    EMAIL = 254
    USERNAME = 150
    ANTHROPONYM = 150
    PASSWORD = 128


class HelpText:
    USERNAME = (
        f"Максимум {MaxLength.USERNAME} символов. Допускаются "
        "буквы, цифры и символы @/./+/- ."
    )
    ANTHROPONYM = f"Не более {MaxLength.ANTHROPONYM} символов"
    PASSWORD = f"Не более {MaxLength.PASSWORD} символов"
    EMAIL = f"Не более {MaxLength.EMAIL} символов"
