import os
import time
import binascii
import hashlib

class Channel:
	def __init__(self, pk1: str, pk2: str, amount: int, open_date: int):
		self.pk1 = pk1
		self.pk2 = pk2
		self.amount = amount
		self.open_date = open_date
		self.close_date = -1

	def jsonify(self) -> str:
		return "{"+f"\"pk1\":\"{self.pk1}\", \"pk2\":\"{self.pk2}\", \"cap\":{self.amount}, \"open_date\":{self.open_date}, \"close_date\":{self.close_date}"+"}"


def main():
	#Starting block (before block 1120 there are no LN transaction for sure)
	count = 1125
	#count = 0
	path = "./"

	active_channels = {}
	closed_channels = []

	start_time = time.time()
	while count != -1:
		filename = "blk" + "".join(['0' for x in range(5-len(str(count)))]) + str(count) + ".dat"

		if not os.path.exists(path + filename):
			count = -1
			break;

		print("Parsing " + filename)
		data = open(filename,"rb").read()
		position = 0
		rightyear = True

		while position < len(data) and rightyear:
		#PRE-HEADER
		#4byte magicnumber
		#4bite size
			magicnum = readPlain(data[position:position+4])
			size = readSwapHex(data[position+4:position+8])
			position += 8
		#HEADER
		#4byte version
		#32byte prevhash
		#32byte merkleroot
		#4byte time
		#4byte bits
		#4byte nonce
			prevhash = readPlain(data[position+4:position+36])	
			epochtime = readSwapHex(data[position+68:position+72])
			
			print(time.strftime('%d/%m/%Y, %H:%M:%S',time.localtime(epochtime)))

			header = readPlain(data[position:position+80])
			currhash = readSwapEndianness(hashlib.sha256(hashlib.sha256(data[position:position+80]).digest()).digest())
			txposition = position+80
			position += size

		#TRANSACTIONS
		#Varint count
		#Transactions
			txcount, txposition = readVarInt(data, txposition)
			print(currhash, txcount)
			for tx in range(txcount):
		#4byte version
		#Varint inputcount
		#INPUTS
		#Varint outputcount
		#OUTPUTS
				#Remove version
				print("V:",readSwapEndianness(data[txposition:txposition+4]))
				txposition += 5 

				inputcount, txposition = readVarInt(data, txposition)
				print(inputcount)
				txposition += 1
				for txinput in range(inputcount):
					txposition+=36
					sigsize, txposition = readVarInt(data, txposition)
					txposition+=sigsize+4

				outputcount, txposition = readVarInt(data,txposition)
				print(outputcount)
				for txoutput in range(outputcount):
					value = readSwapHex(data[txposition:txposition+8])
					txposition+=8
					scriptsize, txposition = readVarInt(data,txposition)
					script = readPlain(data[txposition:txposition+scriptsize])
					txposition+=scriptsize

					if script.startswith("52") and script.endswith("52ae"):
						print(script)
						sys.exit(0)

				#filter out the transaction
				locktime = readSwapHex(data[txposition:txposition+4])
				print(readPlain(data[txposition:txposition+60]))
				print()
				txposition+=4
		count += 1
		print("--- %s seconds ---" % (time.time() - start_time))

	output_string = "{\"channels\":["
	for chan in closed_channels:
		output_string += chan.jsonify() + ","
	output_string = output_string[0:-1]
	output_string += "]}"

	with open("channels.json","w") as f:
		f.write(output_string)

def readPlain(array: list[bytes]) -> str:
	return binascii.hexlify(array).decode("utf-8")

def readSwapEndianness(array: list[bytes]) -> str:
	swap = readPlain(array)
	#split (for), reverse([::-1]) and merge(join) all together
	return "".join([swap[i:i+2] for i in range(0, len(swap), 2)][::-1])

def readSwapHex(array: list[bytes]) -> int:
	return int(readSwapEndianness(array),16)

def readVarInt(array: list[bytes], position: int) -> (int, int):
	txvarint = readSwapHex(array[position:position+1])
	position+=1

	if txvarint == 0xfd:
		print("\t\t0xfd")
		txvarint = readSwapHex(array[position:position+2])
		position+=2
	elif txvarint == 0xfe:
		txvarint = readSwapHex(array[position:position+4])
		position+=4
	elif txvarint == 0xff:
		txvarint = readSwapHex(array[position:position+8])
		position+=8

	return txvarint, position
