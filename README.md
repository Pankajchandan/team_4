### Drive4good

### APIs
##### Get Deficit items to view what Items are needed and in what quantity
GET http://drive4good-surprised-antelope.mybluemix.net/get_items</br>

##### Donate Items
POST http://drive4good-surprised-antelope.mybluemix.net/donate_item</br>
Body:</br>
{
            "d_name": "Sam Johnson",
            "d_phone": "213213212",
            "addr": "1 Washington Sq San Jose, CA 95116",
            "items": {
                "bedsheets": "1",
                "mineral water": "1",
                "scarfs": "1",
                "sugar": "1",
                "comforter": "1",
                "pillow": "1"
            }
}

##### Driver View addresses to pickup from
POST http://drive4good-surprised-antelope.mybluemix.net/driver_see_pickups</br>
Body:</br>
{
	"addr":"428 S 11th Street, San Jose, CA"
}

##### Driver picks up items and the inventory gets updated
POST http://drive4good-surprised-antelope.mybluemix.net/pickup_item
Body:</br>
{
	"pickup_1": "12345"
}

#### compute_resource
POST http://drive4good-surprised-antelope.mybluemix.net/compute_resource
Body:</br>
{
	"disaster_type": "hurricane",
	"category": "category 1",
	"population": "10000"
}

### Deployment and monitoring
Deployed as a service on IBM cloud foundry </br>
ELK for log management and seraching</br>
Availibility Monitoring for availibility and alerting</br>
