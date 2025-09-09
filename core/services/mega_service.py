import os
import tempfile
from mega import Mega

MEGA_EMAIL = os.getenv("MEGA_EMAIL")
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD")

class MegaService:
    def __init__(self, email: str = None, password: str = None):
        email = email or MEGA_EMAIL
        password = password or MEGA_PASSWORD
        if not email or not password:
            raise RuntimeError("MEGA_EMAIL / MEGA_PASSWORD non configurés.")
        self._m = Mega().login(email, password)

    def upload_path(self, file_path: str):
        """Upload depuis un chemin local. Retourne (handle, share_link, download_link)."""
        node = self._m.upload(file_path)          # retourne un objet/dict 'node'
        handle = None
        if isinstance(node, dict) and "h" in node:
            handle = node["h"]

        # Obtenir un lien public
        share_link = None
        try:
            # certaines versions
            share_link = self._m.get_link(node)
        except Exception:
            try:
                share_link = self._m.get_upload_link(node)
            except Exception:
                pass

        # Exporter (rend public) si nécessaire
        if not share_link:
            try:
                exported = self._m.export(node)
                # exported peut être str ou dict selon versions
                share_link = exported if isinstance(exported, str) else exported.get("link")
            except Exception:
                pass

        # download_link = souvent égal à share_link (MEGA calcule le direct à partir du lien public)
        download_link = share_link
        if not handle and share_link:
            # tentative d'extraire le handle depuis l'URL
            # ex: https://mega.nz/file/<HANDLE>#<KEY>
            try:
                handle = share_link.split("/file/")[1].split("#")[0]
            except Exception:
                pass

        if not handle:
            raise RuntimeError("Impossible d'obtenir le handle MEGA après upload.")

        return handle, share_link, download_link

    def upload_fileobj(self, fileobj, filename: str):
        """Upload depuis un file-like object (request.FILES['pdf'])."""
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(filename)[1] or ".pdf")
        os.close(fd)
        with open(tmp, "wb") as out:
            out.write(fileobj.read())
        try:
            return self.upload_path(tmp)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    def delete(self, handle: str):
        """Supprime un fichier MEGA via son handle."""
        try:
            node = self._m.find(handle)
            if node:
                self._m.delete(node)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la suppression du fichier MEGA: {e}")
        finally:
            pass

    def get_file_info(self, handle: str):
        """Retourne les métadonnées d'un fichier MEGA via son handle."""
        try:
            node = self._m.find(handle)
            if node:
                return self._m.get_node_info(node)
            return None
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération des infos du fichier MEGA: {e}")