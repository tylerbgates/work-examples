'''
This tool will take in a folder full of PDFs and convert ALL of the files into .png or .jpeg, you decide
with an input number 1 or 2
requires Python 3.x
'''

import os
import pdf2image


def convert_pdf_2_img():
    pdf_path = input(r"Filepath to All PDFs: ")
    filetype = input(r"Enter 1 for PNG, 2 for JPEG: ")

    # check to see if folder / files exist
    if os.path.isdir(pdf_path) == True:
        pass
    else:
        print("file location not found; check path")
        convert_pdf_2_img()
        return

    # filetype output selection
    if filetype == "1":
        suffix = ".png"
        type = "PNG"
    elif filetype == "2":
        suffix = ".jpeg"
        type = "JPEG"
    else:
        "Wrong option, come on there are only 2 options"
        convert_pdf_2_img()
        return

    # convert all PDFs in folder to images
    for filename in os.listdir(pdf_path):
        if not filename.endswith(".pdf"):
            pass
        else:
            print(filename)
            images = pdf2image.convert_from_path(str(filename))
            # save pdf pages as images
            for i in range(len(images)):
                images[i].save('page'+str(i) + suffix, type)


convert_pdf_2_img()
