from html.parser import HTMLParser
from urllib.request import urlopen
import csv
import json
import boto3

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.should_print = False
        self.result = []
        self.url = ""
    def handle_starttag(self, tag, attrs):
        if not self.should_print and tag in ("pre") :
            self.should_print = True

    def handle_endtag(self, tag):
        if self.should_print and tag in ("pre") :
            self.should_print = False

    def handle_data(self, data):
        content = data.strip()
        if self.should_print and content:
            arr = content.split("\r\n\r\n")
            for pub in arr:
                obj = {}
                current_property = ""
                for line in pub.splitlines():
                    if line[0].isalpha():
                        t = line.partition("-")
                        current_property = t[0].strip()
                        if not current_property in obj:
                            if current_property == "DP":
                                obj[current_property] = t[2].strip().partition(" ")[0]
                            else:
                                obj[current_property] = t[2].strip()
                        elif current_property == "PT":
                            obj[current_property] += "\n" + t[2].strip()
                    else:
                        obj[current_property] += " " + line.strip()
                self.result.append(obj)

            filename = 'pubmed-result.csv'
            with open("/tmp/" + filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')

                writer.writerow(["Titre", "Auteur", "Date", "Type", "Link"])
                for r in self.result:
                    link = "https://pubmed.ncbi.nlm.nih.gov/" + r["PMID"]
                    writer.writerow([r["TI"], r.get("AU") or r.get("CN") or "", r["DP"], r["PT"], link])
            bucket = "pubmed-sql.click"
            s3 = boto3.client("s3")
            s3.upload_file("/tmp/" + filename, bucket, filename)
            self.url = "https://s3.eu-west-3.amazonaws.com/" + bucket + "/" + filename



def getPubmed(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    data = json.loads(event['body'])
    if 'url' in data:
   
        # link = "https://pubmed.ncbi.nlm.nih.gov/?term=(glucose)+and+(continuous)+and+(monitoring+or+measurement)+and+(diabetes)&filter=pubt.guideline&filter=pubt.meta-analysis&filter=pubt.systematicreview&filter=datesearch.y_10&filter=hum_ani.humans&filter=lang.english&filter=lang.french&timeline=expanded&format=pubmed&size=200&page=1"
        f = urlopen(data['url'])
        myfile = f.read().decode("utf8")
        parser = MyHTMLParser()
        parser.feed(myfile)

        response = {
            "statusCode": 200,
            "headers": {
                "content-type": "application/json"
            },
            "body": json.dumps(parser.url)
        }
   
        return response
    return {"error": "No URL found in data"}

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
