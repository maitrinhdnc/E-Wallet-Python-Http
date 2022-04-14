import socketserver
from apscheduler.schedulers.background import BackgroundScheduler
from app.controller.merchant_controller import MyHandler
from app.service.transaction_service import TransactionService
    
if __name__=="__main__":
    check_transaction_expire = TransactionService.check_transaction_expire
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_transaction_expire, 'interval', seconds=10)
    scheduler.start()

    Handler = MyHandler
    PORT = 8000
    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), MyHandler) as httpd:
            print(f"Starting http://127.0.0.1:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping by Ctrl+C")
        httpd.server_close() 