with import <nixpkgs> {};

stdenv.mkDerivation {
	name = "nodejs11_python37_search";

	buildInputs = [
		nodejs-11_x
		python3
		python37Packages.tornado
		python37Packages.pandas
		python37Packages.python-docx
		python37Packages.nltk
		python37Packages.requests
	];
}
