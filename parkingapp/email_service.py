"""
Email Notification Service for Smart Parking System
Handles sending emails for receipts, alerts, and notifications
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_parking_receipt(user_email, receipt_text, invoice_data):
        """Send parking receipt via email"""
        subject = f"Parking Receipt - {invoice_data['invoice_id']}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; color: white; text-align: center;">
                <h2>Smart Parking System</h2>
                <p>Parking Receipt</p>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9;">
                <h3>Invoice: {invoice_data['invoice_id']}</h3>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Transaction ID:</td>
                        <td style="padding: 10px;">{invoice_data['transaction_id']}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Entry Time:</td>
                        <td style="padding: 10px;">{invoice_data['entry_time']}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Exit Time:</td>
                        <td style="padding: 10px;">{invoice_data['exit_time']}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Amount Due:</td>
                        <td style="padding: 10px; color: #667eea; font-weight: bold; font-size: 18px;">
                            {invoice_data['currency']} {invoice_data['amount']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Status:</td>
                        <td style="padding: 10px; color: #28a745; font-weight: bold;">{invoice_data['status'].upper()}</td>
                    </tr>
                </table>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <pre style="font-family: monospace; font-size: 12px; white-space: pre-wrap; word-wrap: break-word;">
{receipt_text}
                    </pre>
                </div>
            </div>
            
            <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>If you have any questions, contact us at support@smartparking.com</p>
                <p>&copy; 2024 Smart Parking System. All rights reserved.</p>
            </div>
        </div>
        """
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=receipt_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Receipt email sent to {user_email} for invoice {invoice_data['invoice_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send receipt email: {str(e)}")
            return False
    
    @staticmethod
    def send_parking_reminder(user_email, vehicle_info, parked_duration_hours):
        """Send parking duration reminder"""
        subject = "Parking Duration Reminder - Smart Parking"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #ff9800; padding: 20px; color: white; text-align: center;">
                <h2>Parking Time Alert</h2>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9;">
                <p>Hello!</p>
                <p>Your vehicle has been parked for <strong>{parked_duration_hours:.1f} hours</strong>.</p>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <p><strong>Vehicle Details:</strong></p>
                    <p>License Plate: {vehicle_info.get('plate', 'N/A')}</p>
                    <p>Vehicle Type: {vehicle_info.get('type', 'N/A')}</p>
                </div>
                
                <p>Please ensure your vehicle is not left unattended for extended periods.</p>
            </div>
            
            <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>Smart Parking System - Keeping your parking worry-free</p>
            </div>
        </div>
        """
        
        text_content = f"""
Parking Time Alert

Your vehicle ({vehicle_info.get('plate', 'N/A')}) has been parked for {parked_duration_hours:.1f} hours.

Please ensure your vehicle is not left unattended for extended periods.

Smart Parking System
"""
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Reminder email sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send reminder email: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_confirmation(user_email, transaction_data):
        """Send payment confirmation"""
        subject = f"Payment Confirmed - {transaction_data['transaction_id']}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #4caf50; padding: 20px; color: white; text-align: center;">
                <h2>✓ Payment Confirmed</h2>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9;">
                <p>Your payment has been processed successfully!</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Transaction ID:</td>
                        <td style="padding: 10px;">{transaction_data['transaction_id']}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">Amount:</td>
                        <td style="padding: 10px; font-weight: bold; color: #4caf50;">
                            INR ₹{transaction_data['amount']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Date:</td>
                        <td style="padding: 10px;">{transaction_data['timestamp']}</td>
                    </tr>
                </table>
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #2e7d32; margin: 0;"><strong>Status: COMPLETED</strong></p>
                </div>
            </div>
            
            <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>Thank you for your payment!</p>
                <p>For support: support@smartparking.com</p>
            </div>
        </div>
        """
        
        text_content = f"""
Payment Confirmed

Transaction ID: {transaction_data['transaction_id']}
Amount: INR ₹{transaction_data['amount']}
Date: {transaction_data['timestamp']}
Status: COMPLETED

Thank you for your payment!
"""
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Payment confirmation sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_alert_notification(user_email, alert_type, alert_message):
        """Send general alert notification"""
        alert_subjects = {
            'unauthorized': 'Security Alert - Unauthorized Vehicle Detected',
            'full': 'Parking Lot Full Alert',
            'maintenance': 'Maintenance Notification',
            'payment_pending': 'Payment Required',
            'system': 'System Notification'
        }
        
        subject = alert_subjects.get(alert_type, 'Smart Parking Alert')
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2196F3; padding: 20px; color: white; text-align: center;">
                <h2>Alert Notification</h2>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9;">
                <p>{alert_message}</p>
            </div>
            
            <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>Smart Parking System</p>
            </div>
        </div>
        """
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=alert_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Alert email sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False
