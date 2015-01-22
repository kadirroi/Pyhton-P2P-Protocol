import socket
import threading
import errno
import time
import glob
import os
import hashlib
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import Queue
import struct
from Tkinter import *
import math
import tkMessageBox
from random import randint
import random
import sqlite3


#**************************************Global Fonksiyonlar**********************************************************     
#Peer klasörünün içine  gitmeye  çalışılıyor
def  go_peer_dictionary():
     global dictionary
     if os.path.join(os.path.expandvars("%userprofile%"),"Desktop")==os.getcwd():
          os.chdir(dictionary)
     else:
          os.chdir(os.path.join(os.path.expandvars("%userprofile%"),"Desktop",dictionary))     


#veritabanı  varmı yokmu
def open_db(database_name):
     #Peer klasörünün içine  gitmeye  çalışılıyor
     go_peer_dictionary()  
     #Peer  klasöründe  databasen var olup olmadığı kontrol ediliyor  tekrar database oluşturmamak için

     if os.path.isfile(database_name):
          return True
     return False
#veritabanı  peer  klasöründe
def  create_database(database_name):
  if open_db(database_name):
    con = sqlite3.connect(database_name,check_same_thread = False)
    
    with con:
      cur = con.cursor()
  else:
    try:
      con = sqlite3.connect(database_name,check_same_thread = False)
      print "yok"
      with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE [md5sums] ([md5_id] INTEGER  PRIMARY KEY NULL,[md5sum] TEXT  NULL,[file_name] TEXT  NULL,[chunk_number_size] INTEGER  NULL)")
        cur.execute("CREATE TABLE chunk_numbers (def_id INTEGER PRIMARY KEY, chunk_number INTEGER,"
                    "md5_def INTEGER, FOREIGN KEY(md5_def) REFERENCES md5sums(md5_id))")
        
    except sqlite3.Error:
      print "Error open db.\n"
  return cur,con

#Bu fonksiyon veritabanında mdsum ve onun chunk sayıları  çekecektir. 
def get_mdssum_chunklist():
     global liste_chunk
     chk_nbr=[]
     cur,con=create_database(database_name)
     cur.execute("SELECT md5sum  FROM md5sums")
     data=cur.fetchall()
     if len(data)!=0:
          for  item in data:
               liste_chunk[item[0]]=chk_nbr
               
          for  item_chunk in  liste_chunk:
                md5_id=get_md5_id(item_chunk,cur )
                for item_chunks in get_chunk_number(md5_id,cur):
                      liste_chunk[item_chunk].append(item_chunks)
          con.close()            
     return liste_chunk                
               
#Bu fonksiyon veritabanından md5sum  file tablodan  id sini çekiyor.              
def get_md5_id(file_md5sum,cur):
     cur.execute("SELECT md5_id  FROM md5sums WHERE md5sum='%s' " % file_md5sum)
     data=cur.fetchall()
     return data[0][0]

#Bu fonksiyon    veritabanında chunk numaralarının listesini çekmekte   
def get_chunk_number(md5_id,cur):
     cur.execute("SELECT chunk_number  FROM  chunk_numbers  WHERE md5_def=?",(md5_id,))
     data=cur.fetchall()
     return data
     
                   

#************************************************ VERİTABANI KISMI************************************************
class Database():
    def __init__(self):
         self.database_name='torrent_db1.db'
    #bu fonksiyon veritabanı bağlantısnı sağlamakta
    def connect(self):
         self.cur,self.con =create_database(self.database_name)
         return self.cur,self.con
  
    #Bu fonksiyon database  md5sum numaralarını ekliyor  eklemeyi sağlıyor
    def insert_data_md5(self,file_md5sum,file_name,chunk_number_size):
         self.cur.execute("""INSERT INTO md5sums VALUES(NULL, ?,?,?)""",(file_md5sum,file_name,chunk_number_size))
         self.con.commit()
         return "Suc"

    #Bu fonksiyon database  gelen chunkların  numaralarını ekliyor  eklemeyi sağlıyor
    def insert_data_chunk_number(self,chunk_number,file_md5sum):
         self.cur.execute("""INSERT INTO chunk_numbers VALUES(NULL, ?,?)""",(int(chunk_number), self.get_md5sum_id(file_md5sum)))
         self.con.commit()
         return "Suc"
     
     
    #Bu fonksiyon veritabanında  dosyanın md5nin   idsini çekiyor     
    def get_md5sum_id(self,file_md5sum):
         self.cur.execute("SELECT md5_id from md5sums where md5sum='%s' " %file_md5sum)
         data=self.cur.fetchall()
         return data[0][0]

    #Bu fonksiyon databasedeki  md5suma göre  dosyanın ismini çekiyor
    def get_file_name(self,file_md5sum):
         
         self.cur.execute("SELECT file_name from md5sums where md5sum='%s' " %file_md5sum)
         data=self.cur.fetchall()
         return data[0][0]

    #Bu fonksiyonda  databasedeki md5sumın  kaç tane  olduğunu gösterir 
    def  get_chunk_number_size(self,file_md5sum):
        
         self.cur.execute("SELECT chunk_number_size from md5sums where md5sum='%s' " %file_md5sum)
         data=self.cur.fetchall()
         if len(data[0])==1:
              return data[0][0]
         return "Q"
     #Bu fonksiyon databasede  inen dosyanın kaçtane   chunkının indmiş olduğunu gösterir 
    def get_chunk_number_list(self,file_md5sum):
         
         self.cur.execute("SELECT count(*) FROM chunk_numbers AS c  JOIN md5sums AS md5 ON c.md5_def=md5.md5_id where   md5.md5sum='%s' " %file_md5sum)
         data=self.cur.fetchone()[0]
         return int(data)
     
     #Bu fonksiyon veritabanından indirilmekten olan dosya isimlerini çeker
    def get_list_file_name(self):
         self.cur.execute("SELECT file_name,md5sum from md5sums " )
         data=self.cur.fetchall()
         return data
    #Bu fonksiyon md5sum listesindeki md5sum  varmı yokmu onu  kontrol edebilmektedir    
    def  check_md5sum_number_md5list(self,file_md5sum):
         
         self.cur.execute(" SELECT id from md5sum_list where md5='%s' " %file_md5sum)
         data=self.cur.fetchall()
         if len(data)==0:
              return False
         else:
              return True     

    #Bu fonksiyon  md5sum  varmı yokmu onu  kontrol edebilmektedir    
    def  check_md5sum_number(self,file_md5sum):
         
         self.cur.execute(" SELECT md5_id from md5sums where md5sum='%s' "% file_md5sum)
         data=self.cur.fetchall()
         if len(data)==0:
              return False
         else:
              return True     

     
      #Bu fonksiyon databasede  chunklistesinde  o chunk  var mı yok mu kontrolu  yapmaktadır.Varsa fonksiyon  true yok ise false  döndürmektedir    
    def check_chunk_number(self,chunk_number,file_md5sum):
         chunk_number=int(chunk_number)
         t=(file_md5sum,chunk_number,)
         self.cur.execute("SELECT c.def_id FROM chunk_numbers AS c  JOIN md5sums AS md5 ON c.md5_def=md5.md5_id where md5.md5sum=? and c.chunk_number=?",t )
         data=self.cur.fetchall()
         if len(data)==0:
              return False
         else:
              return True
     #Bu  fonksiyon dosya  indirildikten sonra  veritabanındaki indirilen dosyaya  ait   herşeyi siler
    def  delete_md5sum_number(self,file_md5sum):
         md5_id=self.get_md5sum_id(file_md5sum)
         t=(md5_id,)
         self.cur.execute("DELETE FROM md5sums WHERE md5sum='%s' " % file_md5sum)
         self.cur.execute("DELETE FROM  chunk_numbers WHERE md5_def=? ",t)
         self.con.commit()







#*******************************************Peerin server tarafı**********************************************

class  ServerThread(threading.Thread):
     def __init__(self, name, peer_ip, peer_port):
        threading.Thread.__init__(self)
        self.name = name
        self.peer_ip=peer_ip
        self. peer_port=peer_port
       
        
     def run(self):
          peer_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          peer_socket.bind(( self.peer_ip,self. peer_port))
          peer_socket.listen(5)
          threadCounter=0
          while True:
              cPeer,addrPeer=peer_socket.accept() 
              threadCounter += 1
              threadPeer = ServerReadThread("ServerReadThread"+str(threadCounter), cPeer, addrPeer)
              threadPeer.start()
              
#******************************************Peerin server tarafı okuması**************************************

class ServerReadThread (threading.Thread):
    def __init__(self, name, cSocket, address):
        threading.Thread.__init__(self)
        self.name = name
        self.cSocket = cSocket
        self.address = address
        self.peer_ip=""
        self.peer_port=""
        self.connect_point={}
        self.check_command_nummber=""
        self.msg_list=""
        self.file_name_list=""
        self.user_add=""
        self.running=True
        
        
       
    def parser(self,data) :
         global connect_point_list
         global connect_point_temp_list
         global CHUNK_SIZE
         global dictionary
         global liste_chunk
         global md5_folder
         
         if data[0:5]=="HELLO" :
              response = "SALUT"
              self.cSocket.send(response)
         elif data[0:5]=="CLOSE":
              response = "BUBYE"
              self.cSocket.send(response)
              self.cSocket.close()
         elif data[0:5]=="REGME":
              self.peer_ip=str(data[6:data.index(":")])
              self.peer_port=data[data.index(":")+1:]
             
              
              if  self.peer_ip+str(self.peer_port)  in connect_point_temp_list.keys():
                   response = "REGOK"
                   
                   try:
                        self.cSocket.send(response)
                   except socket.error:
                        self.cSocket.close()
                   self.check_command_nummber=2
                        
              else:
                   t=time.ctime()
                   self.connect_point["time"]=t
                   self.connect_point["peer_port"]= self.peer_port
                   self.connect_point["peer_ip"]=self.peer_ip
                   self.user_add=self.peer_ip+":"+str(self.peer_port)+":"+str(t)
                   connect_point_list.append(self.user_add)
                   connect_point_temp_list[self.peer_ip+str(self.peer_port)]="True"
                   try:
                        self.cSocket.send("REGWA")
                   except socket.error:
                        self.cSocket.close()
                   time.sleep(0.4)     
                   try:
                        self.cSocket.send("REGOK "+str(t))
                   except socket.error:
                        self.cSocket.close()
                   self.check_command_nummber=1
                   self.cSocket.close()
              print(connect_point_list)    
         elif data[0:5]=="GETNL":
              if len(data)>5:
                   if len(connect_point_list)>5:
                        size_list=5
                   else:
                        size_list=len(connect_point_list)
                        
              else:
                   size_list=len(connect_point_list)
                   
              for  user  in  connect_point_list[0: size_list] :   
                   self.msg_list=self.msg_list+user+"\n"
              self.cSocket.send("NLIST BEGIN"+"\n"+self.msg_list+"NLIST END")
              self.cSocket.close()
              print("NLIST BEGIN"+"\n"+self.msg_list+"NLIST END")
              print(self.msg_list)
              print("Listeyi gönderdim")
                   
         elif data[0:11]=="NLIST BEGIN":
              print("GELEN"+data)
              connect_point_list=[]
              connect_point_list=data.split("\n")
              connect_point_list=connect_point_list[1:-1]
              print(connect_point_list)
              connect_point_temp_list.clear()
              for  i  in connect_point_list:
                   tempdiz=i.split(":")
                   connect_point_temp_list[tempdiz[0]+tempdiz[1]]="True"     
              self.cSocket.close()
              print("Guncel listeyi aldım")
              
         elif data[0:5]=="FINDF":
              flag=False
              file_name=data[6:].split(".")
              #Peer klasörünün içine  gitmeye  çalışılıyor
              go_peer_dictionary()
              for file_t in glob.glob("*.*"):
                   if file_name[0] in file_t:
                        flag=True
              if flag:
                   for file_t in glob.glob(file_name[0]+".*"):
                        self.file_name_list=self.file_name_list+file_t+":"+str(self.md5_func(str(file_t)))+":"+str(os.path.getsize(str(file_t)))+"\n"
                   self.cSocket.send("NAMEY BEGIN"+"\n"+self.file_name_list+"NAMEY END")
                   self.cSocket.close()
              else:
                   self.cSocket.send("NAMEN "+data[6:])
                   
         elif data[0:5]=="FINDM":
              md5sum_file=data[6:]
               #Dosyanın hepsi  inmiş olabilir      
              if  md5sum_file in  md5_folder:
                   self.cSocket.send("MSUMY "+md5sum_file)
              #Dosyanın iniyor olabilir   
              elif md5sum_file in liste_chunk.keys():
                   self.cSocket.send("MSUMY "+md5sum_file)
               #Dosya  yok
              else:
                   try:
                        self.cSocket.send("MSUMN "+md5sum_file)
                        self.cSocket.close()
                        self.stop()
                   except  socket.error:
                        self.cSocket.close()
                        
         elif data[0:5]=="FINDC":
              print("folder")
              print (md5_folder)
              md5sum_file=data[6:data.index(":")]
              chunk_number=data[data.index(":")+1:]
              
                  #Dosyanın hepsi  inmiş olabilir    
              if  md5sum_file in  md5_folder:
                   self.cSocket.send("CHNKY "+data[6:])
                  #Dosyanın iniyor olabilir     
              elif chunk_number in liste_chunk[md5sum_file]:
                    try:
                         self.cSocket.send("CHNKY "+data[6:])
                    except socket.error:
                         print("")
                        
                  #Dosya  yok
              else:
                   try:
                        self.cSocket.send("CHNKN "+data[6:])
                        self.cSocket.close()
                        self.stop()
                   except socket.error:
                        self.cSocket.close()
                        
 
         elif data[0:5]=="GETCH":
              md5sum_file=data[6:data.index(":")]
              chunk_number=data[data.index(":")+1:]
              md5={}
              #Peer klasörünün içine  gitmeye  çalışılıyor
              go_peer_dictionary()
              for file in glob.glob("*.*"):
                   md5[self.md5_func(file)]=file
                  #Dosyanın hepsi  inmiş olabilir    
              if  md5sum_file in  md5:
                   file_nam=md5[md5sum_file]
                   self.cSocket.send("CHUNK "+data[6:])
                   time.sleep(0.5)
                   self.cSocket.send(self.chunk_read_file(file_nam,chunk_number))
                   
              #Dosyanın iniyor olabilir     
              elif chunk_number in liste_chunk[md5sum_file]:
                   self.cSocket.send("CHUNK "+data[6:])
                   time.sleep(0.5)
                   self.cSocket.send(self.chunk_read(md5sum_file,chunk_number))
                      
                #Dosya yok   
              else:
                   try:
                        self.cSocket.send("CHNKN "+data[6:])
                        self.cSocket.close()
                        
                   except socket.error:
                        self.cSocket.close()
                        
         else:
              response = "REGER"
              try:
                   self.cSocket.send(response)
                   self.cSocket.close()
              except socket.error:
                   self.cSocket.close()

    def stop(self):
         self.running = False                  
    #İndirilmiş  olan  dosyanın  md5'ni almakiçin kullanılan  fonksiyon
    def md5_func(self,file_name):
         md5 = hashlib.md5()
         with open(file_name,'rb') as filb:
              for ch in iter(lambda: filb.read(8192), b''):
                   md5.update(ch)
              filb.close()     
         return str(md5.hexdigest())
     
    #İndirilmiş  olan  dosyadan bir  chunk okumak için kullanılan fonksiyon  
    def  chunk_read(self,file_md5sum,chunk_number):
         #Peer klasörünün içine  gitmeye  çalışılıyor
         go_peer_dictionary()
         #dosyadan byte  okuyoruz
         with open("."+file_md5sum+"."+"chunk","rb") as filr:
              filr.seek((int(chunk_number)-1)*int(CHUNK_SIZE))
              data=filr.read(int(CHUNK_SIZE))
              filr.close()
              return data
     
    #İndiriliyor  olan  dosyadan bir  chunk okumak için kullanılan fonksiyon    
    def  chunk_read_file(self,file_name,chunk_number):
         #Peer klasörünün içine  gitmeye  çalışılıyor
         go_peer_dictionary()
         #dosyadan byte  okuyoruz
         with open(file_name,"rb") as fila:
              fila.seek((int(chunk_number)-1)*int(CHUNK_SIZE))
              data=fila.read(int(CHUNK_SIZE))
              fila.close()         
              return data
     
    def run(self):
         while self.running:
              try:
                    incoming_data=self.cSocket.recv(8192)
                   
              except socket.error ,e:
                   err=e.args[0]
                   if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                      time.sleep(1)
                      print 'No data available'
                      continue
              self.parser(incoming_data)
             
              if incoming_data=="CLOSE":
                   break
              if incoming_data[0:5]=="REGME":
                   if   self.check_command_nummber==1:
                        break
              elif incoming_data[0:5]=="GETNL":
                   if   self.check_command_nummber==2:
                        break                           
              elif incoming_data[0:5]=="FINDF":
                   if   self.check_command_nummber==2:
                        break    
              elif incoming_data[0:5]=="GETCH":
                   break
              elif incoming_data[0:5]=="REGER":
                   break
              elif incoming_data[0:11]=="NLIST BEGIN":
                   break  
#----------------------------------------------------------------Clientın okuma threadi----------------------------------------
class ClientReadThread (threading.Thread):
    def __init__(self, name, cSocket,list_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.cSocket = cSocket
        self.file_name_list=""
        self.list_queue=list_queue
        self.count=0
        self.connect_point_temp={}
        self.chk_nbr=""
        self.flag_random=True
        self.count2=0
        self.flag_chunk=False
        self.file_name=""
        self.chunk_number=""
        self.file_mdsum=""
        
        
    def parser(self,data):
         global command
         global connect_point_list
         global peer_host
         global peer_port
         global count
         global file_name_list
         global dictionary
         global connect_point_temp_list
         global liste_chunk
    
         
         if data[0:11]=="NAMEY BEGIN":
              self.file_name_list=data.split("\n")
              self.file_name_list=self.file_name_list[1:-1]
              print(self.file_name_list)
             
              file_name_list=self.file_name_list
              self.list_queue.put(self.file_name_list)
              self.cSocket.close()
         elif data[0:5]=="NAMEN":
              self.cSocket.close()
              print(data)    
         elif data[0:5]=="REGWA":
             print("REGWA")
         elif data[0:5]=="MSUMY":
          
              #Burada  random repeati engellemeye çalışılor
              while self.flag_random:
                   database=Database()
                   cur,con=database.connect()
                   if data[6:] in liste_chunk.keys() :
                        valeur=database.get_chunk_number_size(data[6:])
                        #Buradaki  Q değeri veritabanı hatası engellemek için kullanılmaktadır
                        if valeur!="Q":
                             self.chk_nbr=str( random.randint(1, valeur))
                             #Burada databaseden  o chunk numarası  daha önceden varmı diye   kontrol ediliyor
                             if self.chk_nbr in  liste_chunk[data[6:]] :
                                  self.flag_random=True
                             else:
                                  self.flag_random=False
                                  print("Random:"+self.chk_nbr)
                                  print("FINDC "+str(data[6:])+":"+str(self.chk_nbr))
                                  self.cSocket.send("FINDC "+str(data[6:])+":"+str(self.chk_nbr))
                                  
                        else:
                             self.flag_random=False
                           
         elif data[0:5]=="MSUMN":
              self.cSocket.close()
              print(data)
     
         elif data[0:5]=="CHNKY":
              print(data)
              self.cSocket.send("GETCH "+data[6:])
          
         elif data[0:5]=="CHNKN":
              self.cSocket.close()
              print(data)
         elif data[0:5]=="CHUNK":
              self.flag_chunk=True
              chunk_data=data[6:].split(":")
              self.chunk_number=chunk_data[1]
              self.file_mdsum=chunk_data[0]
              print(chunk_data)
         #Burada bayrak değeri true olunca  gelen data  parserdan geçip  bu kısma  giriyor.
         elif self.flag_chunk :
              database=Database()
              cur,con=database.connect()
              if  database.check_md5sum_number(self.file_mdsum) :
                   chunks_numbers=database.get_chunk_number_size(self.file_mdsum)
                   if database.check_chunk_number(self.chunk_number,self.file_mdsum):
                        con.close()
                        self.cSocket.close()
                   else:
                      
                        database.insert_data_chunk_number(self.chunk_number,self.file_mdsum)
                        print(self.chunk_write(self.file_mdsum,self.chunk_number,data))
                        liste_chunk[self.file_mdsum].append(self.chunk_number)
                        self.cSocket.close()
                        #Burada databasede bulunan toplam chunk sayısı ile indirilen chunk sayısı  eşitmidiye  sorgulanıyor
                        if database.get_chunk_number_list(self.file_mdsum)==chunks_numbers:
                             print(database.get_chunk_number_list(self.file_mdsum))
                             file_name=database.get_file_name(self.file_mdsum)
                             self.rename_file(file_name,self.file_mdsum)
                             print(file_name)
                             #Veritabanı  indirilen dosyaya ait  herşey  siliniyor
                             database.delete_md5sum_number(self.file_mdsum)
                             del liste_chunk[self.file_mdsum]  
                             print("Dosya indirildi")
              
              
                                  
                                  
                             
         elif data[0:5]=="REGOK":
              
              if len(data)>6:   
                   if count==0:
                        print("REGOK")
                        self.cSocket.close()
                        self.check_comman=0
                        time.sleep(1)
                        #Negatorun ip ve port bilgisi
                        server_host="127.0.0.1"
                        server_port=12345
                        #Peerin clienti ilk olarak negatora bağlanıyor
                        se=socket.socket()
                        se.connect((server_host,server_port))
                       
                        se.send("REGME "+peer_host+":"+str(peer_port))
                        command="GETNL"
                        time.sleep(0.3)
                        
                        count=1
                         #Peerin client tarafının okuması
                        client_read=ClientReadThread("PeerServerReadThread",se,self.list_queue)
                        client_read.start()

                   elif command[0:5]=="FINDF":
                        for  connection in connect_point_list:
                             connection=connection.split(":")
                             per_ip=connection[0]
                             per_port=connection[1]
                         
                             if  per_port!=str(peer_port):
                                  s=socket.socket()
                                  s.connect((per_ip,int(per_port)))
                                  time.sleep(0.3)
                                  s.send("REGME "+peer_host+":"+str(peer_port))
                                
                                  #Peerin client tarafının okuması
                                  client_read=ClientReadThread("PeerServerReadThread",s,self.list_queue)
                                  client_read.start()                        
              else:
                   print(command)
                   try:
                        self.cSocket.send(command)
                   except socket.error:
                         self.cSocket.close()
              
         elif data[0:5]=="REGER":
              print("REGER")
                 
         elif data[0:11]=="NLIST BEGIN":
              connect_point_list=data.split("\n")
              connect_point_list=connect_point_list[1:-1]
              print(connect_point_list)
              for  i  in connect_point_list:
                   tempdiz=i.split(":")
                   connect_point_temp_list[tempdiz[0]+tempdiz[1]]="True"     
              self.cSocket.close()
              print("güncelipeerden aldım")
              
    #Dosyaya byte  yazmak için kullanıla  fonksiyon
    def  chunk_write(self,file_md5sum,chunk_number,data):
         #Peer klasörünün içine  gitmeye  çalışılıyor
         go_peer_dictionary()  
         with open("."+file_md5sum+"."+"chunk","rb+") as fils:
              fils.seek((int(chunk_number)-1)*int(CHUNK_SIZE))
              fils.write(data)
              fils.close()  
         return "Succesful Chunk"
     
    #ikikez  dosya indirdiğinde  aynı olan dosyalara  farklı isim veriyor
    def rename_file(self,file_name,file_md5):
         flag=True
         count=0
         while flag:
              if not os.path.isfile(file_name):
                   os.rename("."+file_md5+".chunk",file_name)
                   flag=False
              else:
                   count+=1
                   file_name=file_name[:file_name.index(".")]+"("+str(count)+")"+file_name[file_name.index("."):];
      
              
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
              
              if incoming_data[0:5]!="CHUNK":
                   self.parser(incoming_data)
              else:
                   
                   self.parser(incoming_data)
                   try:
                        self.parser(self.cSocket.recv(4096))
                        self.flag_chunk=False
                        break
                   except  socket.error:
                        self.cSocket.close()
                   

             
              if str(incoming_data[0:11])=="NLIST BEGIN":
                   break
                   
              if str(incoming_data[0:5])=="REGOK":
                   if len(incoming_data)>5:
                        break
      
              if incoming_data[0:11]=="NAMEY BEGIN":
                   break                 
           
              if incoming_data[0:5]=="CHNKN":
                   break
              if incoming_data[0:5]=="NAMEN":
                   break
              if incoming_data[0:5]=="MSUMN":
                   break    
       
                    
#Arama sonuçlarını listeler
class interface_list_show (threading.Thread):
     def __init__(self, name, Lb1,threadQueue):
          threading.Thread.__init__(self)
          self.name = name
          self.Lb1=Lb1
          self.list_queue = threadQueue
     def run(self):
          while True:
               if  self.list_queue.qsize>0:
                    count_item=0
                    msg_queu=self.list_queue.get()
                    for item in msg_queu:
                         count_item+=1
                         self.Lb1.insert(count_item, item)
                         
                         
#Dosya indirmek için kullanılan thread    
class download_file_Thread (threading.Thread):
     def __init__(self, name,down_file_name,list_queue):
          threading.Thread.__init__(self)
          self.down_file_name = down_file_name
          self.list_queue=list_queue
          self.name_file=""
          self.counter=0
         

     def run(self):
          
          global connect_point_list
          global peer_host
          global peer_port
          global command
          database=Database()
          cur,con=database.connect()
          self.name_file=self.down_file_name.split(":")
          while True:
               if  database.check_md5sum_number(self.name_file[1]):
                    for user in  connect_point_list:
                         user_ip_port=user.split(":")
                         if peer_port!=int(user_ip_port[1]):
                              #Burada  peer  güncel listeyi almadan sitemde  olmayan bir kullanıcıya   bağlantı kurmaya  çalışabilir.Bu durum engellenmiştir.
                              try:
                                   sok=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                   sok.connect((user_ip_port[0],int(user_ip_port[1])))
                                   sok.send("FINDM "+self.name_file[1])
                              except socket.error  as e:
                                   if e.errno == errno.ECONNREFUSED:
                                        sok.close()
                                        
                              self.counter+=1
                              client_read=ClientReadThread("PeerServerReadThread"+str(self.counter),sok,self.list_queue)
                              client_read.start()
                         time.sleep(1)
               else:
                    break
        
#Bu thread diğer  peerlerden   güncel olan listeyi  istiyor                
class ClientGetUpdateList (threading.Thread):
    def __init__(self, name,list_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.list_queue=list_queue
    def run(self):
         global command
         global UPDATE_INTERVAL
         while True:
              time.sleep(UPDATE_INTERVAL)
              number= random.randint(1, 2)
              if number==1:
                   command="GETNL "+"5"
              else:
                   command="GETNL "
                   
              for  connection in connect_point_list:
                   connection=connection.split(":")
                   per_ip=connection[0]
                   per_port=connection[1]
                   print(per_port)
                   if  per_port!=str(peer_port):
                        print("Güncel listeyi peer")
                        s=socket.socket()
                        s.connect((per_ip,int(per_port)))
                        s.send("REGME "+peer_host+":"+str(peer_port))
                        client_read=ClientReadThread("PeerServerReadThread",s,self.list_queue)
                        client_read.start()

#Bu thread   peerin dosyasında  indirilmiş  ve paylaşıma açılmış olan dosyaların md5sum listesini tutumaktadır                
class Md5sumList (threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    def run(self):
         global md5_folder
         while True:
              md5_folder=self.md5_list_folder()
              print(md5_folder)
              time.sleep(25)
              
    def md5_list_folder(self):
         md5_diz=[]
        
         go_peer_dictionary()
         for file in glob.glob("*.*"):
              md5_diz.append(self.md5_func(file))
         return md5_diz
    #İndirilmiş  olan  dosyanın  md5'ni almakiçin kullanılan  fonksiyon
    def md5_func(self,file_name):
         md5 = hashlib.md5()
         with open(file_name,'rb') as filb:
              for ch in iter(lambda: filb.read(8192), b''):
                   md5.update(ch)
              filb.close()     
              return str(md5.hexdigest())               
          
               
     
          
#***********************************************User Interface**************************************************              
class interface:
  def __init__(self, parent,queue):
    self.list_queue=queue
    self.root=parent
    GUIFrame =Frame(parent,width= 600, height=500)
    GUIFrame.pack(expand = True, anchor = CENTER)
    self.entry = Entry(text="enter your choice",font = "Helvetica 16 bold",justify="left",width=34,bd=1)
    self.entry.place(x=20, y = 10)
    self.test = StringVar()
    self.test.set('''Arama Sonuçları''')
    self.Label3 = Label(parent, textvariable = self.test)
    self.Label3.place(x = 20, y = 40)
    self.Lb1 = Listbox(parent,width=68,height=10)
    self.Lb1.place(x=20,y=60)
    self.Lb2 = Listbox(parent,width=68,height=10)
    self.Lb2.place(x=20,y=250)
    self.test = StringVar()
    self.test.set('''Tamamlanmayan dosyalar ''')
    self.Label1 = Label(parent, textvariable = self.test)
    self.Label1.place(x = 20, y = 230)
    self.Button2 = Button(parent, text='BUL',command=self.Find_File,padx=50,pady=2)
    self.Button2.place(x= 450, y = 10)
    self.Button3 = Button(parent, text='ÇIKIŞ', command= self.exit_program,padx=50,pady=2)
    self.Button3.place(x= 450, y = 470)

    self.Lb1.bind('<<ListboxSelect>>', self.immediately)
    self.Lb2.bind('<<ListboxSelect>>', self.immediately2)
    self.listbox_items()
    self.listbox_not_complete()
   
   
  def immediately(self,e):
       w = e.widget
       index = int(w.curselection()[0])
       value = w.get(index)
       print 'You selected item %d: "%s"' % (index, value)
       self.download_file(value)
  def immediately2(self,e):
       w = e.widget
       index = int(w.curselection()[0])
       value = w.get(index)
       print 'You selected item %d: "%s"' % (index, value)
       self.download_file_continue(" "+":"+value)
       
  def  download_file_continue(self,dow_file_name):
       result=tkMessageBox.askquestion("Download", "Are you sure?", icon='warning')
       if result=='yes':
            down_fil=download_file_Thread("DownThread",dow_file_name,self.list_queue)
            down_fil.start()
       else:
            print "Vazgeçti"
  def download_file(self,dow_file_name):
    global liste_chunk
    result=tkMessageBox.askquestion("Download", "Are you sure?", icon='warning')
    if result=='yes':
        database=Database()
        cur,con=database.connect()
        #Peer klasörünün içine  gitmeye  çalışılıyor
        go_peer_dictionary()  
        name_file=dow_file_name.split(":")  
        self.create_empty_file(name_file[1],name_file[2])
        liste_chunk[name_file[1]]=[]
        database.insert_data_md5(name_file[1],name_file[0],self.calculation_chunk_number(name_file[2]))
        print "Download"
        con.close()
        time.sleep(2)
        down_fil=download_file_Thread("DownThread",dow_file_name,self.list_queue)
        down_fil.start()

    else:
        print "Vazgeçti"
  def listbox_items(self):
       list_box_show=interface_list_show("ListBox",self.Lb1,self.list_queue)
       list_box_show.start()
  def  listbox_not_complete(self):
       if  len(liste_chunk.keys())!=0:
            count_item=0
            for item in liste_chunk.keys():
                 print(item)
                 count_item+=1
                 self.Lb2.insert(count_item, item)
      
  
                      
  def calculation_chunk_number(self,file_size):
       global CHUNK_SIZE
       chunk_numbers=float(file_size)/float(CHUNK_SIZE)
       chunk_numbers=math.ceil(chunk_numbers)
       return int(chunk_numbers)
  def  exit_program(self):
       self.root.destroy()  
       sys.exit()

      
  #Boş dosya  oluşturmak için kullanılan fonksiyon
  def create_empty_file(self,file_md5,file_size):
       with open("."+file_md5+"."+"chunk","wb") as file_create:
            file_create.close()            
  def Find_File(self):
       global command
       test = self.entry.get()
       command="FINDF "+test
       for  connection in connect_point_list:
            connection=connection.split(":")
            per_ip=connection[0]
            per_port=connection[1]
            print(per_port)
            if  per_port!=str(peer_port):
                 print("okey")
                 s=socket.socket()
                 s.connect((per_ip,int(per_port)))
                 s.send("REGME "+peer_host+":"+str(peer_port))
                
                 client_read=ClientReadThread("PeerServerReadThread",s,self.list_queue)
                 client_read.start()
    
             
      
#************************************************Main*********************************************************
#Peer buaralıklarda diğer peerleden güncel liste isteği bulunmaktadır.
UPDATE_INTERVAL=30
#peerin dosyalarının bulunduğu klasör
dictionary="peer"
#Chunklistesi  ve  md5sum listesi  için database
database_name='torrent_db1.db'
#Peerin  kullanıcı listesi
connect_point_list=[]
connect_point_temp_list={}
#Peerin  client  tarafındaki  istemcinin komutları
command=""
temp=""
#Bu değişken negatora  kayıt  işleminde  bayrak olarak kullanılmaktadır.
count=0
#Her chunka ait  chunk boyutu belirtilmektedir.
CHUNK_SIZE=4096

#Burada  peerin indirilmiş olanpaylaşıma açık olan dosyaların  mdsumlsistesini tutyoruz
md5_folder=[]
md5_list_thread=Md5sumList("Md5sumlist")
md5_list_thread.start()

file_name_list=[]
#chunk_listesi  veritabanından çekilmiş
#Burada indirilmesi  tamamlanmayan  dosyaya ait  veritabanından  gerekli chunk ve  mdsum bilgileri çekilip  listeye atılıyor
#Bu sayede  indirilmesi tamamlanmış dosyayı indirmeye devam edebileceğiz
liste_chunk={}
liste_chunk=get_mdssum_chunklist()



#Bulunan dosyaların  arayüzle  haberleşmesi
list_queue=Queue.Queue()
q=Queue.Queue()

#Peerin Ip  ve  port  bilgisi
peer_host="127.0.0.1"
peer_port=12331


#Negatorun ip ve port bilgisi
server_host="127.0.0.1"
server_port=12345

#Peerin Sunucu  tarafı  çalışmaya  başlar
server_peer=ServerThread("ServerThread",peer_host,peer_port)
server_peer.start()

#Peerin clienti ilk olarak negatora bağlanıyor
s=socket.socket()
s.connect((server_host,server_port))


#Peer  negatora  bağlandıktan sonra  otomatik olarak ilk REGME  kaydolma isteğini  gönderiyor  daha sonra 2 saniye sonrada  GETNL  isteği yapıyor
s.send("REGME "+peer_host+":"+str(peer_port))

#Peerin client tarafının okuması
client_read=ClientReadThread("PeerServerReadThread",s,list_queue)
client_read.start()

#--------------------------------------------------------------Peerin Client  tarafı-------------------------------------------------

root = Tk()
root.resizable(width=FALSE, height=FALSE)
MainFrame =interface(root,list_queue)
root.title('Torrent1')

root.mainloop()


              


     




