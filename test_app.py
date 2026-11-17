import unittest
import os
import tempfile
import app as aplicacion


class PruebasAGROSPACE(unittest.TestCase):

    def setUp(self):
        self.archivo_temporal = tempfile.NamedTemporaryFile(delete=False)
        self.archivo_temporal.close()

        self.base_original = aplicacion.DATABASE
        aplicacion.DATABASE = self.archivo_temporal.name
        aplicacion.app.config["TESTING"] = True
        self.cliente = aplicacion.app.test_client()
        aplicacion.crear_tablas()

    def tearDown(self):
        aplicacion.DATABASE = self.base_original
        os.unlink(self.archivo_temporal.name)

    def registrar_usuario(self):
        return self.cliente.post("/registro", data={
            "nombre": "Usuario Prueba",
            "correo": "prueba@test.com",
            "password": "prueba123"
        }, follow_redirects=True)

    def iniciar_sesion(self):
        return self.cliente.post("/login", data={
            "correo": "prueba@test.com",
            "password": "prueba123"
        }, follow_redirects=True)

    def test_inicio(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)

    def test_registro(self):
        respuesta = self.registrar_usuario()
        self.assertEqual(respuesta.status_code, 200)

    def test_inicio_sesion(self):
        self.registrar_usuario()
        respuesta = self.iniciar_sesion()
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Panel de administraci", respuesta.data)

    def test_registro_cultivo(self):
        self.registrar_usuario()
        self.iniciar_sesion()

        respuesta = self.cliente.post("/cultivos/nuevo", data={
            "terreno": "Terreno de prueba",
            "cultivo": "Papa",
            "area": "2.5",
            "observaciones": "Prueba automatizada"
        }, follow_redirects=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Papa", respuesta.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)