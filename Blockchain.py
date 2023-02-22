import datetime
import json
import hashlib

class Blockchain():

    def __init__(self):
        self.chain = []
        self.create_block(proof=1, previous_hash="Genesis Block", voter="Genesis Block", vote="Genesis Block")

    def create_block(self, proof, previous_hash, vote, voter):
        block = {
            "index" : len(self.chain) + 1,
            "timestamp" : str(datetime.datetime.now()),
            "proof" : proof,
            "previous_hash" : previous_hash,
            "vote" : vote,
            "voter" : voter
        }

        encoded_block = json.dumps(block, sort_keys=True).encode()
        encoded_block = hashlib.sha256(encoded_block).hexdigest()
        hash = encoded_block

        block = {
            "1_index" : len(self.chain) + 1,
            "2_voter" : voter,
            "3_vote" : vote,
            "4_timestamp": str(datetime.datetime.now()),
            "5_hash" : hash,
            "6_previous_hash" : previous_hash,
            "7_proof": proof, 
        }

        self.chain.append(block)
        return block

    def previous_block(self):
        previous_block = self.chain[-1]
        return previous_block

    def previous_hash(self):
        last_block = self.chain[-1]
        previous_hash = last_block['5_hash']
        return previous_hash

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:

            proof = str((new_proof ** 2) - (previous_proof ** 2))
            proof = proof.encode()
            hash_function = hashlib.sha256(proof).hexdigest()

            if hash_function[:5] == "00000":
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def generate_hash(self, block):
        coded_block = json.dumps(block, sort_keys=True).encode()
        coded_block_hash = hashlib.sha256(coded_block).hexdigest()
        return coded_block_hash

    def valid_chain(self, chain):
        previous_block = self.chain[-1]
        index = len(self.chain)

        while index < len(chain):
            block = chain[index]

            if block["6_previous_hash"] != self.previous_hash(previous_block):
                return False

            previous_proof = previous_block["proof"]

            current_proof = block["proof"]

            proof = str((current_proof ** 2) - (previous_proof ** 2))

            hash_function = hashlib.sha256(proof).encode().hexdigest()

            if hash_function[:5] != "00000":
                return False

            previous_block = block
            index += 1

        return True