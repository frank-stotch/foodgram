class MaxLength:
    UNIT = 16
    NAME = 256
    SLUG = 50


class Minimum:
    AMOUNT = 1
    COOKING_TIME = 1


class InvalidMessage:
    AMOUNT = f"Хотя бы {Minimum.AMOUNT} ед. выбранного ингредиента!"
    COOKING_TIME = f"Хотя бы {Minimum.COOKING_TIME} мин. готовки!"
    UNIT = f"Не более {MaxLength.UNIT} символов"


class HelpText:
    NAME = f"Не более {MaxLength.NAME} символов"
    COOKING_TIME = f"Хотя бы {Minimum.COOKING_TIME} мин. готовки!"
    AMOUNT = f"Хотя бы {Minimum.AMOUNT} ед. выбранного ингредиента!"
    UNIT = f"Не более {MaxLength.UNIT} символов"
    SLUG = f"Не более {MaxLength.SLUG} символов, обязан быть уникальным"
