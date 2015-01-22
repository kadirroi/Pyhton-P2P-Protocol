import  socket
import time
import threading
import errno
import Queue

#client 
class ClientThread (threading.Thread):
    def __init__(self, name,queue,msg_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.queue=queue
        self.msg_queue=msg_queue
        self.peer_ip=""
        self.peer_port=""
        self.Counter=0
        
    def run(self):
        global connect_point_list
        while True:
            if self.queue.qsize()>0:
                que_msg=self.queue.get()
                self.peer_ip=que_msg[0]
                print("ip:"+self.peer_ip)
                self.peer_port=que_msg[1]
                print("ip:"+str(self.peer_port))
                #Negator peere bağlantı yapamassa  REGER  cevabını döndürüyor.
                try:
                    client_Socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_Socket.connect((self.peer_ip,  self.peer_port))
                except socket.error as e:
                    if e.errno == errno.ECONNREFUSED:
                        del connect_point_list[self.peer_ip+str(self.peer_port)]
                        msg_queue.put("REGER")
                        client_Socket.close()
                   
                client_Socket.send("HELLO")
                client_read = ClientReadThread("ClientReadThread "+str(self.Counter),  client_Socket, self.peer_ip,self.peer_port, self.msg_queue)
                client_read.start()
            
#Client  Soket  okuması
class ClientReadThread(threading.Thread):
      def __init__(self, name, client_socket,peer_ip,peer_port,msg_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.peer_ip =peer_ip
        self.peer_port = peer_port
        self.client_socket=client_socket
        self.server_msg_list=""
        self.msg_queue=msg_queue
      def parser(self,data):
         
          if data[0:5]=="SALUT":
              self.msg_queue.put("REGOK")
             
              global connect_point_list
              t=time.ctime()   
              connect_point_list[self.peer_ip+str(self.peer_port)]["status"]="s"
              connect_point_list[self.peer_ip+str(self.peer_port)]["time"]=t
              print(connect_point_list)
              
              self.client_socket.send("CLOSE")
          elif data[0:5]=="BUBYE":
              self.client_socket.close()
         
      def run(self):
            while True:
                try:
                    incoming_data=self.client_socket.recv(4096)
                except socket.error ,e:
                    err=e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        time.sleep(1)
                        print 'No data available'
                        continue
                print("Client:"+incoming_data)     
                self.parser(incoming_data)
                if(incoming_data)=="BUBYE":
                    break
                
#Bu thread 120 sn bir listedeki bağlantıların devam edip  etmediğini kontorl etmekte                
class ClientTestForever(threading.Thread):
      def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
                          
      def run(self):
          global TEST_INTERVAL
          while True:
              time.sleep(TEST_INTERVAL)
              global connect_point_list
              if len(connect_point_list)>0:
                  for key in  connect_point_list.keys():
                      try:
                          client_test_Socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                          client_test_Socket.connect((connect_point_list[key]["peer_ip"], connect_point_list[key]["peer_port"] ))
                      except socket.error as e:
                          if e.errno == errno.ECONNREFUSED:
                              try:
                                  del connect_point_list[connect_point_list[key]["peer_ip"]+str(connect_point_list[key]["peer_port"])]
                              except KeyError:
                                  pass
                      client_test_Socket.close()        
              time.sleep(5)
              
#Bu thread 10 sn de bir güncel listeyi tüm peerlere  gönderiyor                
class ClientSendUpdateList(threading.Thread):
      def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.msg_list_update=""
                          
      def run(self):
          global UPDATE_INTERVAL
          while True:
              time.sleep(UPDATE_INTERVAL)
              global connect_point_list
              #sistem de  kayıtlı kişi  sayısı  birden fazla  ise  
              if len(connect_point_list)>1:
                  for key in  connect_point_list.keys():
                      try:
                          client_test_Socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                          client_test_Socket.connect((connect_point_list[key]["peer_ip"], connect_point_list[key]["peer_port"] ))
                      except socket.error as e:
                          if e.errno == errno.ECONNREFUSED:
                              try:
                                  del connect_point_list[connect_point_list[key]["peer_ip"]+str(connect_point_list[key]["peer_port"])]
                              except KeyError:
                                  pass
                             
                      for key in  connect_point_list.keys():
                          self.msg_list_update=self.msg_list_update+connect_point_list[key]["peer_ip"]+":"
                          self.msg_list_update=self.msg_list_update+str(connect_point_list[key]["peer_port"])+":"
                          self.msg_list_update=self.msg_list_update+connect_point_list[key]["time"]+"\n"
                      client_test_Socket.send("NLIST BEGIN"+"\n"+self.msg_list_update+"NLIST END")
                      self.msg_list_update=""
                      print(connect_point_list.keys())
                      print("Güncel Listeyi gönderdim")   
                      client_test_Socket.close()        
              time.sleep(5)
              
          
                    
          
        

#-----------------SERVER------------------------------------------------------------------------------
#Server Soket  Okuması              
class ReadThread (threading.Thread):
    def __init__(self, name, cSocket, address,queue,msg_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.cSocket=cSocket
        self.queue=queue
        self.address = address
        self.peer_ip=""
        self.peer_port=""
        self.connect_point={}
        self.Counter=0
        self.msg_list=""
        self.check_command_nummber=""
        self.msg_queue=msg_queue
        #and data[5]=="" and not data[6:data.index(":")]=="" and not  data[data.index(":")+1:]==""
    def parser(self,data) :
        global connect_point_list
       
        if data[0:5]=="REGME" :
            self.peer_ip=str(data[6:data.index(":")])
            self.peer_port=int(data[data.index(":")+1:])
            
            if  self.peer_ip+str(self.peer_port)  in connect_point_list:
                response = "REGOK"
                try:
                    self.cSocket.send(response)
                except socket.error:
                    self.cSocket.close()
                    
                self.check_command_nummber=2
            else:
                self.connect_point["time"]=" "
                self.connect_point["status"]="w"
                self.connect_point["peer_port"]= self.peer_port
                self.connect_point["peer_ip"]=self.peer_ip
                connect_point_list[self.peer_ip+str(self.peer_port)]=self.connect_point
                response = "REGWA"
                self.cSocket.send(response)
                self.queue.put((self.peer_ip,self.peer_port))
                self.check_command_nummber=1
                time.sleep(0.4)
                
                if self.msg_queue.get()=="REGOK":
                    t=time.ctime()    
                    self.cSocket.send("REGOK"+str(t))
                    self.cSocket.close()
                else:
                    self.cSocket.send("REGER")
                    self.cSocket.close()
                    
                    
                    
                
                
        elif data[0:5]=="GETNL":
            for key in  connect_point_list.keys():
                self.msg_list=self.msg_list+connect_point_list[key]["peer_ip"]+":"
                self.msg_list=self.msg_list+str(connect_point_list[key]["peer_port"])+":"
                self.msg_list=self.msg_list+connect_point_list[key]["time"]+"\n"
            self.cSocket.send("NLIST BEGIN"+"\n"+self.msg_list+"NLIST END")
            self.cSocket.close()
            
            
        else:
            response = "REGER"
            self.cSocket.send(response)
    def run(self):
        while True:
              try:
                  incoming_data=self.cSocket.recv(4096)
              except socket.error ,e:
                  err=e.args[0]
                  if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                      time.sleep(1)
                      print 'No data available'
                      continue
               
              self.parser(incoming_data)
              print("Server:"+incoming_data)
              if incoming_data[0:5]=="REGME":
                  if   self.check_command_nummber==1:
                      break
              elif incoming_data[0:5]=="GETNL":
                  if   self.check_command_nummber==2:
                      break
                
            
              
#-----MAİN-----

#Negator tüm peerlere  bu zaman  aralığında  güncel listeyi gönderiyor.
UPDATE_INTERVAL=10
#Negatorun tüm peerlerin bağlantısını   bu zaman aralığında test  ediyor.
TEST_INTERVAL=120
#Kullanıcılistesi
connect_point_list={}
#Threadler arası haberleşmee
queue=Queue.Queue()
msg_queue=Queue.Queue()
#negatorun  client tarafı
client=ClientThread("Client",queue,msg_queue)
client.start()
#Her 20 saniyede  bir  tüm peerlerin bağlantısını test ediyor
client_test_forever=ClientTestForever("ClientTestForever")    
client_test_forever.start()
#Her 30 saniyede  bir  tüm peerleregüncel  liste  gönderiyor.
client_send_update_list=ClientSendUpdateList("ClientSendUpdateList")
client_send_update_list.start()

#negatorun sunucusu
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host=("127.0.0.1")
port=12345
s.bind((host,port))
s.listen(5)
threadCounter=0
while True:
    c,addr=s.accept()
    print "Got a connection from ", addr
    threadCounter += 1
    thread = ReadThread("ReadThread"+str(threadCounter), c, addr,queue,msg_queue)
    thread.start()
    
