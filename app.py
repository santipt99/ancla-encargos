from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
import base64, io, os

app = Flask(__name__)
CORS(app)

W, H = A4
AZUL = HexColor('#1a3fa0'); VERDE = HexColor('#6b7c1e'); AZUL2 = HexColor('#2d7ab5')
LOGO_B64 = os.environ.get('LOGO_B64', '')

def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL); canvas.rect(0, H-28, W, 28, fill=1, stroke=0)
    canvas.setFillColor(VERDE)
    p = canvas.beginPath(); p.moveTo(0,H-28); p.lineTo(0,H-155); p.lineTo(118,H-28); p.close()
    canvas.drawPath(p, fill=1, stroke=0)
    canvas.setFillColor(AZUL2)
    p2 = canvas.beginPath(); p2.moveTo(0,H-28); p2.lineTo(0,H-130); p2.lineTo(95,H-28); p2.close()
    canvas.drawPath(p2, fill=1, stroke=0)
    if LOGO_B64:
        logo_bytes = base64.b64decode(LOGO_B64)
        logo_img = ImageReader(io.BytesIO(logo_bytes))
        canvas.drawImage(logo_img, 75, H-168, width=175, height=130, preserveAspectRatio=True, mask='auto')
    canvas.setFillColor(AZUL); canvas.rect(0, 0, W, 14, fill=1, stroke=0)
    canvas.restoreState()

class AnclaDoc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(path, pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
                         topMargin=5.8*cm, bottomMargin=1.8*cm)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='body')
        self.addPageTemplates([PageTemplate(id='page', frames=[frame], onPage=draw_page)])

def s(name, **kw):
    base = dict(fontName='Times-Roman', fontSize=10, leading=15, spaceAfter=0, spaceBefore=0, wordWrap='LTR')
    base.update(kw); return ParagraphStyle(name, **base)

S = {
    'body':    s('body', alignment=TA_JUSTIFY, firstLineIndent=1.4*cm),
    'bodyni':  s('bodyni', alignment=TA_JUSTIFY),
    'bullet':  s('bullet', alignment=TA_JUSTIFY, leftIndent=1.0*cm, firstLineIndent=-0.5*cm),
    'htitle':  s('htitle', fontName='Times-Bold', alignment=TA_CENTER, fontSize=12, leading=16),
    'stitle':  s('stitle', fontName='Times-Bold', firstLineIndent=1.4*cm),
    'honsec':  s('honsec', fontName='Times-Bold', firstLineIndent=1.4*cm),
    'rgpd':    s('rgpd', fontSize=8.5, leading=12, alignment=TA_JUSTIFY, spaceAfter=4),
    'sig':     s('sig', alignment=TA_CENTER, fontName='Times-Bold'),
    'signame': s('signame', alignment=TA_CENTER),
}

def sp(h): return Spacer(1, h*mm)
def bul(t): return Paragraph(f'\u2013\u00a0\u00a0\u00a0{t}', S['bullet'])
def hon(imp, conc): return Paragraph(f'\u2013\u00a0\u00a0\u00a0<b><u>{imp}</u></b> {conc}', S['bullet'])
def stitle(t, suf=':'): return Paragraph(f'<u><b>{t}</b></u>{suf}', S['stitle'])
def rgpd(lbl, txt): return Paragraph(f'<b>{lbl}</b>{txt}', S['rgpd'])

def generate_pdf(data):
    buf = io.BytesIO()
    doc = AnclaDoc(buf)
    story = []

    story += [sp(4),
              Paragraph('<u>H O J A \u00a0 D E \u00a0 E N C A R G O \u00a0 P R O F E S I O N A L</u>', S['htitle']),
              sp(8),
              Paragraph(f'<b>{data["tratamiento"]} {data["nombre"]}</b> con DNI {data["dni"]} y con domicilio en {data["domicilio"]} encarga al <b>Despacho ANCLA ABOGADOS S.L.</b>, con domicilio en C/ Concepción Arenal, 2-4, 2º A, 15006, A Coruña, tel. 981278633 y C.I.F. n.º B-70392493 la realización de los siguientes:', S['body']),
              sp(8), stitle('Trabajos profesionales'), sp(3)]

    for t in data['trabajos']:
        story += [bul(t), sp(2)]

    story += [sp(4),
              Paragraph('La ejecución de dichos trabajos profesionales se efectuará en régimen de arrendamiento de servicios y con arreglo a las normas deontológicas de la Abogacía, lo cual significa que no se garantiza el resultado.', S['body']),
              sp(8), stitle('Consideraciones'), sp(3)]

    for c in [
        'Que el ejercicio de la acción pueda ser infructuoso.',
        'Que el Despacho de Abogados podrá delegar, a su criterio, todas o parte de las tareas del presente encargo profesional, en los Abogados colaboradores del despacho profesional, y pueda valerse de otros auxiliares y colaboradores sin que tal hecho incremente el importe de sus honorarios.',
        'Que el Despacho de Abogados se encuentra sujeto a las normas sobre <u>prevención de blanqueo de capitales y financiación del terrorismo</u> establecidas en la <b><u>Ley 10/2010</u></b> y que el encargo encomendado está o puede estar fuera del ámbito de secreto profesional y que, por tanto, queda efectivamente fuera del ámbito de protección, en caso de que las autoridades financieras requieran información sobre los datos obtenidos del cliente o el encargo efectuado, se está obligado a facilitarlo.',
    ]:
        story += [bul(c), sp(3)]

    story += [sp(5), stitle('Honorarios'), sp(3),
              Paragraph('Los honorarios profesionales por los servicios encomendados se desglosan del siguiente modo:', S['body']),
              sp(4), Paragraph(f'<u><b>{data["seccion_honorarios"]}</b></u>', S['honsec']), sp(3)]

    for h in data['honorarios']:
        story += [hon(h['importe'], h['concepto']), sp(2)]

    story += [sp(5),
              Paragraph('A los honorarios indicados se les aplicará el IVA correspondiente (21%). Este presupuesto se corresponde exclusivamente a la primera instancia.', S['bodyni']),
              sp(4),
              Paragraph('Asimismo, todo aquello no contemplado expresamente en el presente presupuesto se minutará aplicando los Criterios de Honorarios del Ilustre Colegio de Abogados de A Coruña.', S['bodyni']),
              sp(5), Paragraph('Conceptos no incluidos:', S['bodyni']), sp(2)]

    for n in [
        'No se incluyen gastos de notarios, procuradores, gastos de envío de telegramas o burofax, peritos, médicos, economistas, asesores o tramitadores fiscales u otros profesionales, ni otros servicios que serán pagados aparte por el cliente de acuerdo con el presupuesto que estos presenten en caso de ser necesarios.',
        'Así mismo, el presente presupuesto no incluye trámites de Seguridad Social, de Inspección de Trabajo y/o SEPEE, de que, en su caso, se presupuestarán y minutarán aparte.',
    ]:
        story += [bul(n), sp(2)]

    story += [sp(4),
              Paragraph('Cancelación anticipada: En caso de cancelación del encargo por parte del cliente, se facturarán las actuaciones realizadas hasta la fecha según el presente presupuesto y los criterios del Ilustre Colegio de Abogados de A Coruña.', S['bodyni']),
              PageBreak(), sp(4)]

    for lbl, txt in [
        ('RESPONSABLE DEL TRATAMIENTO: ', 'ANCLA ABOGADOS SL CIF: B70392493 Dir. Postal: CALLE CONCEPCIÓN ARENAL 2 2º A-E, 15006 - A CORUÑA Teléfono: 981278633 Correo electrónico: lopd@anclabogados.com.'),
        ('FINALIDAD DEL TRATAMIENTO DE SUS DATOS: ', 'Las finalidades legítimas del tratamiento de los datos de carácter personal son la gestión profesional, administrativa, contable y fiscal del encargo, así como el archivo de expedientes.'),
        ('LEGITIMACIÓN: ', 'Artículo 6.1.b) del RGPD. Tratamiento necesario para la ejecución de un contrato en el que el interesado es parte o para la aplicación a petición de éste de medidas precontractuales.'),
        ('CONSERVACIÓN Y TRATAMIENTO DE LOS DATOS: ', 'Los datos de carácter personal proporcionados por el cliente podrán ser comunicados en los escritos y en los documentos anejos a éstos a los Juzgados y Tribunales o, en su caso, Administraciones Públicas, para el cumplimiento del encargo encomendado, así como a procuradores, peritos y otros profesionales. En otro supuesto no se cederán a terceros salvo obligación legal.'),
    ]:
        story.append(rgpd(lbl, txt))

    story += [
        Paragraph('Los datos proporcionados se conservarán mientras se mantenga la relación contractual o durante los años necesarios para cumplir con las obligaciones legales. ANCLA ABOGADOS SL no elaborará ningún tipo de "perfil" en base a la información facilitada ni se tomarán decisiones automatizadas en base a perfiles.', S['rgpd']),
        Paragraph('El cliente se compromete a que toda la información facilitada sea veraz. En todo caso, será el cliente el único responsable de las manifestaciones falsas o inexactas que realice.', S['rgpd']),
        sp(3),
        Paragraph('Asimismo, solicitamos su autorización para:', S['rgpd']),
        Paragraph('Utilización del WhatsApp para comunicaciones de/con la empresa.\u00a0\u00a0\u00a0\u00a0<b>Sí autorizo.</b>\u00a0\u00a0\u00a0\u00a0No autorizo.', S['rgpd']),
        Paragraph('Remitirle comunicaciones e información adicionales no relacionados directamente con este encargo.\u00a0\u00a0\u00a0\u00a0<b>Sí autorizo.</b>\u00a0\u00a0\u00a0\u00a0No autorizo.', S['rgpd']),
        Paragraph('<b>Comunicaciones telemáticas.</b> El cliente autoriza expresamente a la Sociedad ANCLA ABOGADOS S.L.P y personal administrativo a enviarle comunicaciones vía mail, vía sms, o vía mensajería instantánea.', S['rgpd']),
        rgpd('DERECHOS: ', 'Como cliente podrá ejercer los derechos de acceso, rectificación, supresión, oposición, limitación del tratamiento, portabilidad de datos y a no ser objeto de decisiones individualizadas automatizadas, ante el responsable del tratamiento, adjuntando copia de su DNI. En caso de no obtener satisfacción, puede presentar reclamación ante la <i>Agencia Española de Protección de Datos</i>: https://sedeagpd.gob.es'),
        sp(4),
        Paragraph('Los abajo firmantes acuerdan como medio de comunicación preferente para el desarrollo del trabajo el correo electrónico, conociendo y asumiendo el cliente bajo su responsabilidad, que este medio de comunicación puede presentar fallos o vulnerabilidades.', S['rgpd']),
        sp(8),
        Paragraph(f'En A Coruña, a {data["fecha"]}.', S['bodyni']),
        sp(14),
    ]

    story.append(KeepTogether([
        Table([
            [Paragraph('EL CLIENTE,', S['sig']),    Paragraph('EL LETRADO,', S['sig'])],
            [sp(14),                                  sp(14)],
            [Paragraph(data['nombre'],  S['signame']), Paragraph('ANCLA ABOGADOS S.L.', S['signame'])],
            [Paragraph(f'DNI: {data["dni"]}', S['signame']), Paragraph('', S['signame'])],
        ], colWidths=[8.5*cm, 8.5*cm],
           style=TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                             ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('TOPPADDING',(0,0),(-1,-1),0),
                             ('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    ]))

    doc.build(story)
    buf.seek(0)
    return buf

@app.route('/generar', methods=['POST'])
def generar():
    try:
        data = request.get_json()
        buf = generate_pdf(data)
        nombre = data.get('nombre','cliente').replace(' ','_')
        fecha = data.get('fecha','').replace(' ','_')
        filename = f'HojaEncargo_{nombre}_{fecha}.pdf'
        return send_file(buf, mimetype='application/pdf',
                        as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return 'OK'

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
