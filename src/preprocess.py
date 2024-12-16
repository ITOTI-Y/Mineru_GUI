import json
import copy

from loguru import logger
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.pipe.OCRPipe import OCRPipe
from magic_pdf.pipe.TXTPipe import TXTPipe
from magic_pdf.pipe.UNIPipe import UNIPipe
from pathlib import Path

class PDF2MD:
    def __init__(self, pdf_path:str):
        self.pdf_path = Path(pdf_path)

    def run(self, **kwargs):
        try:
            pdf_name = Path(self.pdf_path).stem
            pdf_path_parent = self.pdf_path.parent

            if kwargs.get('output_dir'):
                output_path = Path(kwargs.get('output_dir')).joinpath(pdf_name)
            else:
                output_path = pdf_path_parent.joinpath(pdf_name)

            output_image_path = output_path.joinpath('images')

            image_path_parent = output_image_path.name

            pdf_bytes = open(self.pdf_path, 'rb').read()

            orig_model_list = []

            if kwargs.get('model_json_path'):
                model_json = json.load(open(kwargs.get('model_json_path'), 'r', encoding='utf-8').read())
                orig_model_list = copy.deepcopy(model_json)
            else:
                model_json = []

            image_writer, md_writer = FileBasedDataWriter(output_image_path), FileBasedDataWriter(output_path)
            # 选择解析方式
            if kwargs.get('parse_method') == 'auto':
                jso_useful_key = {'_pdf_type': '', 'model_list': model_json}
                pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
            elif kwargs.get('parse_method') == 'txt':
                pipe = TXTPipe(pdf_bytes, model_json, image_writer)
            elif kwargs.get('parse_method') == 'ocr':
                pipe = OCRPipe(pdf_bytes, model_json, image_writer)
            else:
                logger.error('unknown parse method, only auto, ocr, txt allowed')
                exit(1)

            pipe.pipe_classify()

            # 如果没有传入模型数据，则使用内置模型解析
            if len(model_json) == 0:
                pipe.pipe_analyze()  # 解析
                orig_model_list = copy.deepcopy(pipe.model_list)

            # 执行解析
            pipe.pipe_parse()

            # 保存 text 和 md 格式的结果
            content_list = pipe.pipe_mk_uni_format(image_path_parent, drop_mode='none')
            md_content = pipe.pipe_mk_markdown(image_path_parent, drop_mode='none')

        except Exception as e:
            logger.exception(e)

if __name__ == '__main__':
    pdf_path = 'demo.pdf'
    output_dir = 'output'
    pdf2md = PDF2MD(pdf_path)
    pdf2md.run(output_dir=output_dir, parse_method='auto')
