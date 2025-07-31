import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from decouple import config
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from .models import QuickBooksInvoice
from .serializers import QuickBooksInvoiceSerializer

logger = logging.getLogger(__name__)

class QuickBooksCreateInvoiceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = QuickBooksInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Initialize QuickBooks client
                auth_client = AuthClient(
                    client_id=config('QUICKBOOKS_CLIENT_ID'),
                    client_secret=config('QUICKBOOKS_CLIENT_SECRET'),
                    environment='sandbox',  # Use 'production' for live
                    redirect_uri=config('QUICKBOOKS_REDIRECT_URI'),
                )
                qb_client = QuickBooks(
                    auth_client=auth_client,
                    refresh_token=config('QUICKBOOKS_REFRESH_TOKEN'),
                    company_id=config('QUICKBOOKS_COMPANY_ID'),
                )

                # Prepare invoice data
                invoice_data = serializer.validated_data
                customer_name = invoice_data['customer_name']
                total_amount = invoice_data['total_amount']
                order_number = invoice_data['order_number']

                # Create customer if not exists (simplified)
                from quickbooks.objects.customer import Customer
                customer = Customer()
                customer.DisplayName = customer_name
                customer.save(qb=qb_client)

                # Create invoice
                from quickbooks.objects.invoice import Invoice, Line
                invoice = Invoice()
                invoice.CustomerRef = customer.to_ref()
                line = Line()
                line.Amount = total_amount
                line.Description = f"Invoice for order {order_number}"
                invoice.Line.append(line)
                invoice.save(qb=qb_client)

                # Save to local database with QuickBooks ID
                invoice_instance = serializer.save(qb_invoice_id=invoice.Id)
                logger.info(f"Invoice created in QuickBooks: {invoice.Id}")

                return Response(QuickBooksInvoiceSerializer(invoice_instance).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating QuickBooks invoice: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuickBooksGetInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, qb_invoice_id):
        try:
            # Initialize QuickBooks client
            auth_client = AuthClient(
                client_id=config('QUICKBOOKS_CLIENT_ID'),
                client_secret=config('QUICKBOOKS_CLIENT_SECRET'),
                environment='sandbox',
                redirect_uri=config('QUICKBOOKS_REDIRECT_URI'),
            )
            qb_client = QuickBooks(
                auth_client=auth_client,
                refresh_token=config('QUICKBOOKS_REFRESH_TOKEN'),
                company_id=config('QUICKBOOKS_COMPANY_ID'),
            )

            # Retrieve invoice from QuickBooks
            from quickbooks.objects.invoice import Invoice
            invoice = Invoice.get(qb_invoice_id, qb=qb_client)
            if not invoice:
                return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

            # Update or create local record
            invoice_instance, created = QuickBooksInvoice.objects.update_or_create(
                qb_invoice_id=invoice.Id,
                defaults={
                    'order_number': invoice.DocNumber or 'N/A',
                    'customer_name': invoice.CustomerRef.name or 'Unknown',
                    'total_amount': float(invoice.TotalAmt) if invoice.TotalAmt else 0.0,
                    'status': invoice.Status,
                }
            )

            return Response(QuickBooksInvoiceSerializer(invoice_instance).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving QuickBooks invoice: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)