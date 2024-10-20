from abc import ABC, abstractmethod
from datetime import date, timedelta


# Money class for handling amounts (optional, you can use float/int as well)
class Money:
    def __init__(self, amount: float):
        self.amount = amount

    def __add__(self, other):
        return Money(self.amount + other.amount)

    def __repr__(self):
        return f"${self.amount:.2f}"


# Revenue Recognition class
class RevenueRecognition:
    def __init__(self, amount: Money, recognized_date: date):
        self.amount = amount
        self.recognized_date = recognized_date

    def is_recognizable_by(self, query_date: date) -> bool:
        return query_date >= self.recognized_date

    def __repr__(self):
        return f"Recognition of {self.amount} on {self.recognized_date}"


# Abstract Recognition Strategy class
class RecognitionStrategy(ABC):
    @abstractmethod
    def calculate_revenue_recognitions(self, contract):
        pass


# Complete recognition strategy - recognizes full revenue immediately
class CompleteRecognitionStrategy(RecognitionStrategy):
    def calculate_revenue_recognitions(self, contract):
        contract.add_revenue_recognition(RevenueRecognition(contract.revenue, contract.when_signed))


# Three-way recognition strategy - recognizes revenue in three parts
class ThreeWayRecognitionStrategy(RecognitionStrategy):
    def __init__(self, first_offset: int, second_offset: int):
        self.first_offset = first_offset
        self.second_offset = second_offset

    def calculate_revenue_recognitions(self, contract):
        part = Money(contract.revenue.amount / 3)
        contract.add_revenue_recognition(RevenueRecognition(part, contract.when_signed))
        contract.add_revenue_recognition(RevenueRecognition(part, contract.when_signed + timedelta(days=self.first_offset)))
        contract.add_revenue_recognition(RevenueRecognition(part, contract.when_signed + timedelta(days=self.second_offset)))


# Product class
class Product:
    def __init__(self, name: str, recognition_strategy: RecognitionStrategy):
        self.name = name
        self.recognition_strategy = recognition_strategy

    def calculate_recognitions(self, contract):
        self.recognition_strategy.calculate_revenue_recognitions(contract)


# Contract class
class Contract:
    def __init__(self, revenue: Money, when_signed: date, product: Product):
        self.revenue = revenue
        self.when_signed = when_signed
        self.product = product
        self.revenue_recognitions = []

    def add_revenue_recognition(self, recognition: RevenueRecognition):
        self.revenue_recognitions.append(recognition)

    def recognized_revenue(self, query_date: date) -> Money:
        recognized_amount = Money(0)
        for recognition in self.revenue_recognitions:
            if recognition.is_recognizable_by(query_date):
                recognized_amount += recognition.amount
        return recognized_amount

    def calculate_recognitions(self):
        self.product.calculate_recognitions(self)


# Example usage:
if __name__ == "__main__":
    # Create products with different recognition strategies
    complete_product = Product("CompleteProduct", CompleteRecognitionStrategy())
    three_way_product = Product("ThreeWayProduct", ThreeWayRecognitionStrategy(30, 60))

    # Create contracts
    contract1 = Contract(Money(3000), date.today(), complete_product)
    contract2 = Contract(Money(3000), date.today(), three_way_product)

    # Calculate recognitions
    contract1.calculate_recognitions()
    contract2.calculate_recognitions()

    # Check recognized revenue by a certain date
    print(f"Contract 1 Recognized Revenue on {date.today()}: {contract1.recognized_revenue(date.today())}")
    print(f"Contract 2 Recognized Revenue on {date.today()}: {contract2.recognized_revenue(date.today())}")

    # View details of revenue recognitions
    print(f"Contract 1 Revenue Recognitions: {contract1.revenue_recognitions}")
    print(f"Contract 2 Revenue Recognitions: {contract2.revenue_recognitions}")