import logging
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import OrderCreateSerializer
from .models import Order
from django.utils import timezone
from decouple import config
import urllib3

# Disable SSL warnings (temporary workaround, remove in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Function to convert snake_case to camelCase
def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

# Function to format postal code for ShipStation
def format_postal_code(postal_code: str, country: str) -> str:
    if not postal_code:
        return ""
    postal_code = postal_code.strip()
    if country.upper() == "US" and len(postal_code) == 5 and postal_code.isdigit():
        return postal_code
    elif country.upper() == "US" and len(postal_code) == 9 and postal_code[5] == "-":
        return postal_code
    return postal_code

# Function to create order in ShipStation
def create_shipstation_order(order_data):
    shipstation_url = "https://ssapi.shipstation.com/orders/createorder"
    api_key = config('SHIPSTATION_API_KEY')
    api_secret = config('SHIPSTATION_API_SECRET')

    if not api_key or not api_secret:
        logger.error("ShipStation API credentials not found in .env")
        raise Exception("ShipStation API credentials missing")

    headers = {
        "Host": "ssapi.shipstation.com",
        "Authorization": f"Basic {api_key}:{api_secret}",
        "Content-Type": "application/json"
    }

    shipstation_order = {
        "orderNumber": order_data["order_number"],
        "orderDate": order_data["order_date"].isoformat(),
        "orderStatus": order_data["order_status"],
        "customerEmail": order_data["customer_email"],
        "billTo": {
            to_camel_case(k): format_postal_code(v, order_data["bill_to"]["country"]) if k == "postal_code" else v
            for k, v in order_data["bill_to"].items() if v is not None
        },
        "shipTo": {
            to_camel_case(k): format_postal_code(v, order_data["ship_to"]["country"]) if k == "postal_code" else v
            for k, v in order_data["ship_to"].items() if v is not None
        },
        "items": [
            {
                "sku": item["sku"],
                "name": item["name"],
                "quantity": item["quantity"],
                "unitPrice": item["unit_price"],
                "weight": {
                    "value": item.get("weight_value") or 0,
                    "units": item.get("weight_units") or "pounds"
                }
            }
            for item in order_data["items"]
        ]
    }

    response = requests.post(shipstation_url, headers=headers, json=shipstation_order, verify=False)
    if response.status_code not in [200, 201]:
        logger.error(f"Failed to create ShipStation order: {response.status_code} - {response.text}")
        raise Exception(f"Failed to create ShipStation order: {response.text}")
    logger.info("ShipStation order created successfully")
    return response.json()

class OrderCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Save to local database
                order = serializer.save()

                # Prepare order data for ShipStation
                order_data = serializer.validated_data
                order_data["order_date"] = timezone.now()  # Use current IST time (2025-07-29T18:40:00+05:30)
                create_shipstation_order(order_data)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating order: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
            serializer = OrderCreateSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving order: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)