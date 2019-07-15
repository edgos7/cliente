from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep
import datetime
import openpyxl as excel


terminar = False
pausar = False

def respuestaAutomatica(browser,listaPalabras, listaRespuesta):
    while not terminar:
        noLeidos = browser.find_elements_by_class_name("P6z4j")
        mensaje  = ''
        if len(noLeidos) > 0 and pausar == False:
            ele = noLeidos[-1]
            ele.click()
            try:
                autor = browser.find_element_by_class_name("_19vo_").text  
                mensaje = browser.find_elements_by_class_name("_12pGw")[-1]
                for palabra in listaPalabras:
                    if palabra.lower() in mensaje.text.lower(): 
                        posicion = listaPalabras.index(palabra)
                        cajaTexto = browser.find_element_by_class_name("_3u328")
                        respuesta = autor +" "+ listaRespuesta[posicion]+"\n"
                        cajaTexto.send_keys(respuesta)
                sleep(2)

            except Exception as e:
                print(e)
                pass
        print("respuesta automatica pausada")
    print("Terminado respuesta automatica")


def leerContactos(driver, lista, cont):
	nuevos = 0
	listaContactos = driver.find_elements_by_class_name("_3H4MS")
	ultimo = listaContactos[1]
	for contacto in listaContactos:
		if contacto.text not in lista:
			nuevos+=1
			if cont != 0:
				ultimo=contacto
			lista.append(contacto.text)
	return lista, ultimo, nuevos

def listaContactos(driver):
	contactos =[]
	cont=0
	pausa = 5
	contactos , ultimo, nuevos = leerContactos(driver,contactos,cont)
	while True:
	    driver.execute_script("arguments[0].scrollIntoView();", ultimo )
	    cont+=1
	    contactos, ultimo, nuevos = leerContactos(driver,contactos,cont)
	    if nuevos == 0:
	        break
	return contactos

def leerContactosArchivo(fileName):
    lst = []
    file = excel.load_workbook(fileName)
    sheet = file.active
    firstCol = sheet['A']
    for cell in range(len(firstCol)):
        contact = str(firstCol[cell].value)
        contact = "\"" + contact + "\""
        lst.append(contact)
    return lst


def enviarMensajes(driver, mensaje, contactos,nombres):
    wait = WebDriverWait(driver, 10)
    wait5 = WebDriverWait(driver, 5)
    exitosos = 0
    sNo = 1
    listaErrores = []
    global pausar
    pausar = True
    for target, nombre in zip(contactos, nombres):
        sNo+=1
        try:
            x_arg = '//span[contains(@title,' + target + ')]'
            try:
                wait5.until(EC.presence_of_element_located((
                    By.XPATH, x_arg
                )))
            except:
                inputSearchBox = driver.find_element_by_class_name("_2zCfw")
                sleep(0.5)
                inputSearchBox.clear()
                #newTarget =target[1:len(target) - 1]
                inputSearchBox.send_keys(target)
                sleep(2)

            driver.find_element_by_xpath(x_arg).click()
            sleep(2)
            inp_xpath = "//div[@contenteditable='true']"
            input_box = wait.until(EC.presence_of_element_located((
                By.XPATH, inp_xpath)))
            sleep(1)
            input_box.send_keys(nombre+" "+mensaje)
            sleep(2)
            input_box.send_keys(Keys.ENTER)
            exitosos+=1
            sleep(0.5)

        except:
            driver.get('https://api.whatsapp.com/send?phone=57{}'.format(target))
            try:
                driver.find_element_by_id("action-button").click()
                sleep(10)
                text_box = driver.find_element_by_class_name("_3u328")
                text_box.send_keys(nombre+" "+mensaje)
                text_box.send_keys(Keys.ENTER)
            except:
                driver.get('https://web.whatsapp.com')
                sleep(10)
                print("Cannot find Target: " + target)
                listaErrores.append(target)
    pausar = False
    print("\nEnvios exitosos: ", exitosos)
    print("No se pudo enviar a: ", len(listaErrores))
    print(listaErrores)

def enviarMensajesHora(driver, mensaje, contactos,nombres,hora):
    global pausar
    pausar = True
    exitosos = 0
    listaErrores = []
    while True:
        tiempoActual = datetime.datetime.now()
        horaActual = tiempoActual.time().hour
        minutoActual = tiempoActual.time().minute
        segundoActual = tiempoActual.time().second
        if hora.hour==horaActual and hora.minute==minutoActual and hora.second==segundoActual:
            for target, nombre in zip(contactos, nombres):
                driver.get('https://api.whatsapp.com/send?phone=57{}'.format(target))
                try:
                    driver.find_element_by_id("action-button").click()
                    sleep(10)
                    text_box = driver.find_element_by_class_name("_3u328")
                    text_box.send_keys(nombre+" "+mensaje)
                    text_box.send_keys(Keys.ENTER)
                    exitosos+=1
                except:
                    driver.get('https://web.whatsapp.com')
                    sleep(10)
                    print("Cannot find Target: " + target)
                    listaErrores.append(target)
            pausar = False
            print("\nEnvios exitosos: ", exitosos)
            print("No se pudo enviar a: ", len(listaErrores))
            print(listaErrores)
            

def cambiarTerminar(ter):
    global terminar
    terminar = ter
    
    
