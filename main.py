from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from datetime import datetime, timedelta, date

class bbExampleAlgorithm(QCAlgorithm):

    def Initialize(self):
        ''' Initialize the data and resolution you require for your strategy '''
        
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2020, 9, 7)
        self.__previous = datetime.min
        
        self.CashAmount = 100000.0 #CHANGE HERE
        
        self.SetCash(self.CashAmount)
        
        self.equityDict = dict()
        self.bolDict = dict()
        self.macdDict = dict()

        self.equities = ["TCOM", "BKNG", "GILD" , "INO", "MRNA", "SE", "BABA", "PG", "JNJ"]
        
        for symbol in self.equities:
            self.equityDict[symbol] = self.AddEquity(symbol, Resolution.Daily)
            self.bolDict[symbol] = self.BB(symbol, 20, 2, MovingAverageType.Simple, Resolution.Daily)
            self.macdDict[symbol] = self.MACD(symbol, 12, 26, 9, MovingAverageType.Simple, Resolution.Daily)
            
        self.buyAmount = 1.0/len(self.equities)
        self.sellAmount = -self.buyAmount

        # Set WarmUp period
        self.SetWarmUp(20)
        
    def OnData(self, data):
        
        '''OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.'''
        
        def checkBB(_symbol):
            #Reference: https://www.quantconnect.com/tutorials/strategy-library/the-dynamic-breakout-ii-strategy
            
            # Return if no data or if indicator is not ready
            if not (data.ContainsKey(_symbol) or self.bolDict[_symbol].IsReady): return
    
            # Retrieve current price
            price = self.Securities[_symbol].Close
    
            # Sell if price is higher than upper band
            if not self.Portfolio.Invested and price > self.bolDict[_symbol].UpperBand.Current.Value:
                return "sell"
                
            # Liquidate if price is lower than middle band        
            if self.Portfolio.Invested and price < self.bolDict[_symbol].LowerBand.Current.Value:
                return "buy"
                        
        def checkMACD(_symbol):
            #Reference: https://www.quantconnect.com/forum/discussion/6299/trading-spx500-in-margin-account/p1
        
            # wait for our macd to fully initialize
            if not self.macdDict[_symbol].IsReady: return
    
            # only once per day
            if self.__previous.date() == self.Time.date(): return
    
            # define a small tolerance on our checks to avoid bouncing
            tolerance = 0.0025
    
            holdings = self.Portfolio[_symbol].Quantity
    
            signalDeltaPercent = (self.macdDict[_symbol].Current.Value - self.macdDict[_symbol].Signal.Current.Value)/self.macdDict[_symbol].Fast.Current.Value
    
            # if our macd is greater than our signal, then let's go long
            if holdings <= 0 and signalDeltaPercent > tolerance:  # 0.01%
                # longterm says buy as well
                return "buy"
    
            # of our macd is less than our signal, then let's go short
            elif holdings >= 0 and signalDeltaPercent < -tolerance:
                return "sell"

        for symbol in self.equities:
            
            #stop loss at -20% of portfolion) aka rebalance 
            if self.Portfolio.Cash < 0.8 * self.CashAmount:
                self.stop = True 
                self.Liquidate()
            
            elif checkMACD(symbol) is "sell" and checkBB(symbol) is "sell":
                self.SetHoldings(symbol, self.sellAmount)
                
            elif checkMACD(symbol) is "buy" and checkBB(symbol) is "buy":
                self.SetHoldings(symbol, self.buyAmount)
