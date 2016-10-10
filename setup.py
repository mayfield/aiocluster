from setuptools import setup, find_packages

README = 'README.md'

with open('requirements.txt') as f:
    requirements = f.readlines()


def long_desc():
    try:
        import pypandoc
    except ImportError:
        with open(README) as f:
            return f.read()
    else:
        return pypandoc.convert(README, 'rst')

setup(
    name='aiocluster',
    version='1',
    description='Cluster framework for an AIO service',
    author='Justin Mayfield',
    author_email='tooker@gmail.com',
    url='https://github.com/mayfield/aiocluster/',
    license='MIT',
    long_description=long_desc(),
    packages=find_packages(),
    test_suite='test',
    install_requires=requirements,
    entry_points = {
        'console_scripts': [
            'aiocluster=aiocluster.cli.aiocluster:entry',
            'aiocluster-control=aiocluster.cli.aiocluster_control:entry'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ]
)
