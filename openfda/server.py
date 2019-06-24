import http.server
import http.client
import socketserver
import json


class ClienteOpenFDA:

    def get_info_FDA(self, limit=10, buscar_texto=""):


        req_str = "{}?limit={}".format(FDA_SERVER_JSON, limit)
        if buscar_texto != "":
            req_str += "&{}".format(buscar_texto)
        conn = http.client.HTTPSConnection(FDA_SERVER_API)
        conn.request("GET", req_str, None, http_headers)
        res = conn.getresponse()
        res_json = res.read().decode("utf-8")
        conn.close()
        res = json.loads(res_json)

        if 'results' in res:
            dato = res['results']
        else:
            dato = []
        return dato

    def get_medicaments(self, limit):
        medi_json = self.get_info_FDA(limit)

        return medi_json

    def buscar_med(self, name, limit):
        buscar = "search=active_ingredient:{}".format(name)
        medi_json = self.get_info_FDA(limit, buscar)

        return medi_json

    def buscar_compa(self, name, limit):

        buscar = "search=openfda.manufacturer_name:{}".format(name)
        companies = self.get_info_FDA(limit, buscar)

        return companies

    def get_companies_list(self, limit):

        companies = self.get_info_FDA(limit)

        return companies

    def get_warnings_list(self, limit):
        warnings = self.get_info_FDA(limit)

        return warnings


class OpenFDAHTML:

    def show_error(self):
        with open(ERROR, "r") as f:
            error_html = f.read()

        return error_html

    def show_index(self):
        with open(INDEX, "r") as f:
            index_html = f.read()

        return index_html

    def generate_html_code(self, limit, dato, list_name):
        output = ('<nav><ol class="breadcrumb"><a href="/">In&Iacute;cio</a></ol></nav>'
                  '<h3>Lista de {} de {} artículos.</h3><ul class="list-group">').format(list_name, limit)

        for item in dato:
            output += '<li class="list-group-item">{}</li>'.format(item)
        output += '</ul>'

        return output


class OpenFDAParser:

    def parse_medicament(self, dato):
        medicaments = []
        for item in dato:
            if "openfda" in item:
                try:
                    nombre = item['openfda']['substance_name'][0]
                except KeyError:
                    nombre = "Desconocido"

                try:
                    marca = item['openfda']['brand_name'][0]
                except KeyError:
                    marca = "Desconocido"

                try:
                    fabricante = item['openfda']['manufacturer_name'][0]
                except KeyError:
                    fabricante = "Desconocido"
            else:
                nombre = "Desconocido"
                marca = "Desconocido"
                fabricante = "Desconocido"

            id = item['id']

            try:
                proposito = item['purpose'][0]
            except KeyError:
                proposito = "Desconocido"
            medicaments.append(('<h5>ID:</h5>{} '
                                '<h5>Nombre:</h5>{} '
                                '<h5>Marca:</h5>{} '
                                '<h5>Fabricante:</h5>{} '
                                '<h5>Propósito:</h5>{}').format(id, nombre, marca, fabricante,
                                                                proposito))
        return medicaments

    def parse_companies(self, dato):
        companies = []
        for item in dato:
            if 'openfda' in item and 'manufacturer_name' in item['openfda']:
                companies.append('<h5>Empresa:</h5> {}'.format(item['openfda']['manufacturer_name'][0]))
            else:
                companies.append('<h5>Empresa:</h5> Desconocida')
        return companies

    def parse_warnings(self, dato):
        warnings = []
        for item in dato:
            try:
                nombre = item['openfda']['substance_name'][0]
            except KeyError:
                nombre = "Desconocido"
            if 'warnings' in item and item['warnings']:
                war_msg = item['warnings'][0]
            else:
                war_msg = 'Desconocida'

            warnings.append(('<h5>ID:</h5>{} '
                            '<h5>Advertencias:</h5>{}').format(nombre, war_msg))
        return warnings


class TestHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):

        fda_client = ClienteOpenFDA()
        fda_html = OpenFDAHTML()
        fda_parser = OpenFDAParser()

        mensaje = fda_html.show_index()
        url_path = self.path

        path_array = url_path.split("?")
        metodo = path_array[0]

        if len(path_array) > 1:
            params = path_array[1]
        else:
            params = ""

        limit = 1
        buscar_nombre = ""

        if params:
            if "&" in params:
                params2 = params.split("&")
                parse_name = params2[0].split("=")
                buscar_nombre = parse_name[1]
                parse_limit = params2[1].split("=")
                limit = int(parse_limit[1])
            else:
                parse_array = params.split("=")
                if parse_array[0] == "limit":
                    limit = int(parse_array[1])
                else:
                    limit = 10
                    buscar_nombre = parse_array[1]

        if metodo == "/":
            http_code = 200
        elif "listDrugs" in metodo:
            http_code = 200
            dato = fda_client.get_medicaments(limit)
            dato_parser = fda_parser.parse_medicament(dato)
            mensaje += fda_html.generate_html_code(limit, dato_parser, "medicamentos")
        elif "listCompanies" in metodo:
            http_code = 200
            dato = fda_client.get_companies_list(limit)
            dato_parser = fda_parser.parse_companies(dato)
            mensaje += fda_html.generate_html_code(limit, dato_parser, "empresas")
        elif "buscarDrug" in metodo:
            http_code = 200
            dato = fda_client.buscar_med(buscar_nombre, limit)
            dato_parser = fda_parser.parse_medicament(dato)
            mensaje += fda_html.generate_html_code(limit, dato_parser, "medicamentos")
        elif "buscarCompany" in metodo:
            http_code = 200
            dato = fda_client.buscar_compa(buscar_nombre, limit)
            dato_parser = fda_parser.parse_companies(dato)
            mensaje += fda_html.generate_html_code(limit, dato_parser, "empresas")
        elif "listWarnings" in metodo:
            http_code = 200
            dato = fda_client.get_warnings_list(limit)
            dato_parser = fda_parser.parse_warnings(dato)
            mensaje += fda_html.generate_html_code(limit, dato_parser, "advertencia")
        elif "secret" in metodo:
            http_code = 401
        elif "redirect" in metodo:
            http_code = 302
        else:
            http_code = 404
            mensaje = fda_html.show_error()

        self.send_response(http_code)

        if 'secret' in self.path:
            self.send_header('WWW-Authenticate', 'Basic realm="URL de acceso restringido"')
        elif 'redirect' in self.path:
            self.send_header('Location', 'http://localhost:8000/')

        self.send_header('Content-type', 'text/html')
        self.end_headers()


        self.wfile.write(bytes(mensaje, "utf8"))
        return



HTTP_PORT = 8000
INDEX = "index.html"
ERROR = "404_error.html"
socketserver.TCPServer.allow_reuse_address = True

FDA_SERVER_API = "api.fda.gov"
FDA_SERVER_JSON = "/drug/label.json"
http_headers = {'User-Agent': 'http-client'}

Handler = TestHTTPRequestHandler

httpd = socketserver.TCPServer(("", HTTP_PORT), Handler)
print("serving at port", HTTP_PORT)

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("")
    print("Interrumpido por el usuario")

print("Servidor parado")