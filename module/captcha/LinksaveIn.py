from captcha import OCR
import Image
from os import sep
from os.path import dirname
from os.path import abspath
from glob import glob
import tempfile

from pprint import pprint

class LinksaveIn(OCR):
    def __init__(self):
        OCR.__init__(self)
        self.data_dir = dirname(abspath(__file__)) + sep + "LinksaveIn" + sep
    
    def load_image(self, image):
        im = Image.open(image)
        frame_nr = 0

        lut = im.resize((256, 1))
        lut.putdata(range(256))
        lut = list(lut.convert("RGB").getdata())

        new = Image.new("RGB", im.size)
        npix = new.load()
        while True:
            try:
                im.seek(frame_nr)
            except EOFError:
                break
            frame = im.copy()
            pix = frame.load()
            for x in range(frame.size[0]):
                for y in range(frame.size[1]):
                    if lut[pix[x, y]] != (0,0,0):
                        npix[x, y] = lut[pix[x, y]]
            frame_nr += 1
        new.save(self.data_dir+"unblacked.png")
        self.image = new.copy()
        self.pixels = self.image.load()
        self.result_captcha = ''
    
    def get_bg(self):
        stat = {}
        cstat = {}
        img = self.image.convert("P")
        for bgpath in glob(self.data_dir+"bg/*.gif"):
            stat[bgpath] = 0
            bg = Image.open(bgpath)
            
            bglut = bg.resize((256, 1))
            bglut.putdata(range(256))
            bglut = list(bglut.convert("RGB").getdata())
            
            lut = img.resize((256, 1))
            lut.putdata(range(256))
            lut = list(lut.convert("RGB").getdata())
            
            bgpix = bg.load()
            pix = img.load()
            for x in range(bg.size[0]):
                for y in range(bg.size[1]):
                    rgb_bg = bglut[bgpix[x, y]]
                    rgb_c = lut[pix[x, y]]
                    try:
                        cstat[rgb_c] += 1
                    except:
                        cstat[rgb_c] = 1
                    if rgb_bg == rgb_c:
                        stat[bgpath] += 1
        max_p = 0
        bg = ""
        for bgpath, value in stat.items():
            if max_p < value:
                bg = bgpath
                max_p = value
        return bg
    
    def substract_bg(self, bgpath):
        bg = Image.open(bgpath)
        img = self.image.convert("P")
        
        bglut = bg.resize((256, 1))
        bglut.putdata(range(256))
        bglut = list(bglut.convert("RGB").getdata())
        
        lut = img.resize((256, 1))
        lut.putdata(range(256))
        lut = list(lut.convert("RGB").getdata())
        
        bgpix = bg.load()
        pix = img.load()
        orgpix = self.image.load()
        for x in range(bg.size[0]):
            for y in range(bg.size[1]):
                rgb_bg = bglut[bgpix[x, y]]
                rgb_c = lut[pix[x, y]]
                if rgb_c == rgb_bg:
                    orgpix[x, y] = (255,255,255)
    
    def eval_black_white(self):
        new = Image.new("RGB", (140, 75))
        pix = new.load()
        orgpix = self.image.load()
        thresh = 4
        for x in range(new.size[0]):
            for y in range(new.size[1]):
                rgb = orgpix[x, y]
                r, g, b = rgb
                pix[x, y] = (255,255,255)
                if r > max(b, g)+thresh:
                    pix[x, y] = (0,0,0)
                if g < min(r, b):
                    pix[x, y] = (0,0,0)
                if g > max(r, b)+thresh:
                    pix[x, y] = (0,0,0)
                if b > max(r, g)+thresh:
                    pix[x, y] = (0,0,0)
        self.image = new
        self.pixels = self.image.load()
    
    def run_tesser(self):
        self.logger.debug("create tmp tif")
        tmp = tempfile.NamedTemporaryFile(suffix=".tif")
        self.logger.debug("create tmp txt")
        tmpTxt = tempfile.NamedTemporaryFile(suffix=".txt")
        self.logger.debug("save tiff")
        self.image.save(tmp.name, 'TIFF')
        self.logger.debug("run tesseract")
        self.run(['tesseract', tmp.name, tmpTxt.name.replace(".txt", ""), "nobatch", self.data_dir+"tesser_conf"])
        self.logger.debug("read txt")

        with open(tmpTxt.name, 'r') as f:
            self.result_captcha = f.read().replace("\n", "")

    def get_captcha(self, image):
        self.load_image(image)
        bg = self.get_bg()
        self.substract_bg(bg)
        self.eval_black_white()
        self.to_greyscale()
        self.image.save(self.data_dir+"cleaned_pass1.png")
        self.clean(4)
        self.clean(4)
        self.image.save(self.data_dir+"cleaned_pass2.png")
        letters = self.split_captcha_letters()
        org = self.image
        final = ""
        for n, letter in enumerate(letters):
            self.image = letter
            self.image.save(ocr.data_dir+"letter%d.png" % n)
            self.run_tesser()
            final += self.result_captcha
        
        return final

if __name__ == '__main__':
    import urllib
    ocr = LinksaveIn()
    testurl = "http://linksave.in/captcha/cap.php?hsh=2229185&code=ZzHdhl3UffV3lXTH5U4b7nShXj%2Bwma1vyoNBcbc6lcc%3D"
    urllib.urlretrieve(testurl, ocr.data_dir+"captcha.gif")
    
    print ocr.get_captcha(ocr.data_dir+'captcha.gif')
