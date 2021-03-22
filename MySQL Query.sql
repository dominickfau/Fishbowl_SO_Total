SELECT DATE(NOW()) AS date, SUM(soitem.qtytofulfill - soitem.qtyfulfilled) AS totalQtyOverDue, SUM(soItem.unitPrice * (soitem.qtytofulfill - soitem.qtyfulfilled)) as totalPriceOverDue, totals.*

-- Run this query on a Fishbowl Inventory databaes to generate the raw CSV data file needed.

FROM soitem
    INNER JOIN so ON so.id = soitem.soid
    INNER JOIN product ON product.id = soitem.productid
    CROSS JOIN (SELECT SUM(soitem.qtytofulfill - soitem.qtyfulfilled) AS totalQty, SUM(soItem.unitPrice * (soitem.qtytofulfill - soitem.qtyfulfilled)) as totalPrice
				FROM soitem
					INNER JOIN so ON so.id = soitem.soid
					INNER JOIN product ON product.id = soitem.productid
				WHERE soitem.typeid = 10
				  AND soitem.statusid < 50
				  AND so.statusid IN (20,25)) AS totals

WHERE soitem.typeid = 10
  AND soitem.statusid < 50
  AND so.statusid IN (20,25)
AND soitem.dateScheduledFulfillment < NOW()