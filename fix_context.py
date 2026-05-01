import re

file_path = r'..\trade-spark\src\context\TradingContext.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update signature
old_sig = "executeTrade: (symbol: string, type: 'BUY' | 'SELL', quantity: number, orderType: 'MARKET' | 'LIMIT', limitPrice?: number, productType?: 'NORMAL' | 'INTRADAY') => Promise<boolean>;"
new_sig = "executeTrade: (symbol: string, type: 'BUY' | 'SELL', quantity: number, orderType: 'MARKET' | 'LIMIT', limitPrice?: number, productType?: 'NORMAL' | 'INTRADAY', gttData?: {sl?: number, target?: number}) => Promise<boolean>;"
content = content.replace(old_sig, new_sig)

# Update handler signature
old_handler = "const executeTradeHandler = useCallback(async (symbol: string, type: 'BUY' | 'SELL', quantity: number, orderType: 'MARKET' | 'LIMIT', limitPrice?: number, productType: 'NORMAL' | 'INTRADAY' = 'NORMAL'): Promise<boolean> => {"
new_handler = "const executeTradeHandler = useCallback(async (symbol: string, type: 'BUY' | 'SELL', quantity: number, orderType: 'MARKET' | 'LIMIT', limitPrice?: number, productType: 'NORMAL' | 'INTRADAY' = 'NORMAL', gttData?: {sl?: number, target?: number}): Promise<boolean> => {"
content = content.replace(old_handler, new_handler)

# Update dispatch call
old_dispatch = "order: { symbol: formattedSymbol, side: type, quantity, product_type: productType }"
new_dispatch = "order: { symbol: formattedSymbol, side: type, quantity, product_type: productType, order_type: orderType, limit_price: limitPrice, gtt_sl: gttData?.sl, gtt_target: gttData?.target }"
content = content.replace(old_dispatch, new_dispatch)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated TradingContext.tsx")
