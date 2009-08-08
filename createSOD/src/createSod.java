// Copyright 2009 Jean-Francois Houzard, Olivier Roger
//
// This file is part of epassportviewer.
//
// epassportviewer is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// epassportviewer is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public
// License along with epassportviewer.
// If not, see <http://www.gnu.org/licenses/>.
	
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Security;
import java.security.cert.CertStore;
import java.security.cert.CertificateFactory;
import java.security.cert.CollectionCertStoreParameters;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Vector;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.OptionBuilder;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.commons.cli.PosixParser;

import org.bouncycastle.cms.CMSException;
import org.bouncycastle.cms.CMSProcessable;
import org.bouncycastle.cms.CMSProcessableByteArray;
import org.bouncycastle.cms.CMSSignedData;
import org.bouncycastle.cms.CMSSignedDataGenerator;
import org.bouncycastle.jce.provider.BouncyCastleProvider;

public class createSod {

	private static final String NAME = "createSod";
	private static final String VERSION = "v0.1";

	/**
	 * @param args
	 * @throws CMSException 
	 */
	public static void main(String[] args) throws Exception {
		
		try {
			CommandLine options = verifyArgs(args);
			String privateKeyLocation = options.getOptionValue("privatekey");
			String keyPassword = options.getOptionValue("keypass");
			String certificate = options.getOptionValue("certificate");
			String sodContent = options.getOptionValue("content");
			String sod = "";
			if (options.hasOption("out")){
				sod = options.getOptionValue("out");
			}
			
			// CHARGEMENT DU FICHIER PKCS#12

			KeyStore ks = null;
			char[] password = null;

			Security.addProvider(new BouncyCastleProvider());
			try {
				ks = KeyStore.getInstance("PKCS12");
				// Password pour le fichier personnal_nyal.p12
				password = keyPassword.toCharArray();
				ks.load(new FileInputStream(privateKeyLocation), password);
			} catch (Exception e) {
				System.out.println("Erreur: fichier " +
									privateKeyLocation +
			                       " n'est pas un fichier pkcs#12 valide ou passphrase incorrect");
				return ;
			}

			// RECUPERATION DU COUPLE CLE PRIVEE/PUBLIQUE ET DU CERTIFICAT PUBLIQUE

			X509Certificate cert = null;
			PrivateKey privatekey = null;
			PublicKey publickey = null;

			try {
				Enumeration en = ks.aliases();
				String ALIAS = "";
				Vector vectaliases = new Vector();

				while (en.hasMoreElements())
					vectaliases.add(en.nextElement());
				String[] aliases = (String []) (vectaliases.toArray(new String[0]));
				for (int i = 0; i < aliases.length; i++)
					if (ks.isKeyEntry(aliases[i]))
					{
						ALIAS = aliases[i];
						break;
					}
				privatekey = (PrivateKey)ks.getKey(ALIAS, password);
				cert = (X509Certificate)ks.getCertificate(ALIAS);
				publickey = ks.getCertificate(ALIAS).getPublicKey();
			} catch (Exception e) {
				e.printStackTrace();
				return ;
			}
			
			// Chargement du certificat à partir du fichier

			InputStream inStream = new FileInputStream(certificate);
			CertificateFactory cf = CertificateFactory.getInstance("X.509");
			cert = (X509Certificate)cf.generateCertificate(inStream);
			inStream.close();

			
			// Chargement du fichier qui va être signé

			File file_to_sign = new File(sodContent);
			byte[] buffer = new byte[(int)file_to_sign.length()];
			DataInputStream in = new DataInputStream(new FileInputStream(file_to_sign));
			in.readFully(buffer);
			in.close();

			// Chargement des certificats qui seront stockés dans le fichier .p7
			// Ici, seulement le certificat personnal_nyal.cer sera associé.
			// Par contre, la chaîne des certificats non.

			ArrayList certList = new ArrayList();
			certList.add(cert);
			CertStore certs = CertStore.getInstance("Collection",
								new CollectionCertStoreParameters(certList), "BC");

			CMSSignedDataGenerator signGen = new CMSSignedDataGenerator();

			// privatekey correspond à notre clé privée récupérée du fichier PKCS#12
			// cert correspond au certificat publique personnal_nyal.cer
			// Le dernier argument est l'algorithme de hachage qui sera utilisé

			signGen.addSigner(privatekey, cert, CMSSignedDataGenerator.DIGEST_SHA1);
			signGen.addCertificatesAndCRLs(certs);
			CMSProcessable content = new CMSProcessableByteArray(buffer);

			// Generation du fichier CMS/PKCS#7
			// L'argument deux permet de signifier si le document doit être attaché avec la signature
			//     Valeur true:  le fichier est attaché (c'est le cas ici)
			//     Valeur false: le fichier est détaché

			CMSSignedData signedData = signGen.generate(content, true, "BC");
			byte[] signeddata = signedData.getEncoded();

			// Ecriture du buffer dans un fichier.	

			if (sod.equals("")){
				System.out.print(signeddata.toString());
			}
			else{
				FileOutputStream envfos = new FileOutputStream(sod);
				envfos.write(signeddata.toString());
				envfos.close();
			}
			
			
		} catch (OptionException oe){
			HelpFormatter formatter = new HelpFormatter();
			formatter.printHelp( NAME, getOptions() );
			System.exit(-1);
		} catch (Exception e) {
			e.printStackTrace();
			return ;
		}

	}

	private static CommandLine verifyArgs(String[] args) throws OptionException{
		// create the command line parser
		CommandLineParser parser = new PosixParser();
		
		try {
			CommandLine line = parser.parse( getOptions(), args );
		    // parse the command line arguments
		    
		    if (line.hasOption("v") || line.hasOption("version")){
		    	System.out.println(NAME+" "+VERSION);
				System.out.println("");
				System.out.println(NAME+" packages two unaltered open-source tools:");
				System.out.println(" Apache Common CLI -- commons.apache.org");
				System.out.println(" Bouncy Castle -- www.bouncycastle.org");
				System.out.println("Please see LICENSE files for more informations");		    	
		    	System.exit(0);
		    }
		    
		    List<String> mandatory = new ArrayList<String>();
		    mandatory.add("privatekey");
		    mandatory.add("keypass");
		    mandatory.add("certificate");
		    mandatory.add("content");
		    for (String option : mandatory) {
			    if( !line.hasOption(option ) ) {
			        throw new OptionException("Option " + option + " missing");
			    }
		    }
		    return line;
		}		
		catch( ParseException exp ) {
		    System.out.println( "Unexpected exception:" + exp.getMessage() );
		    System.exit(-1);
		}
		return null;
	}

	// create the Options
	private static Options getOptions() {
		Options options = new Options();
		options.addOption( "v", "version", false, "Version" );
		options.addOption( OptionBuilder.withLongOpt( "privatekey" )
		                                .withDescription( "Private Key Location" )
		                                .hasArg()
		                                .withArgName("path")
		                                .create() );
		
		options.addOption( OptionBuilder.withLongOpt( "keypass" )
						                .withDescription( "Key Password" )
						                .hasArg()
						                .withArgName("string")
						                .create() );
		
		options.addOption( OptionBuilder.withLongOpt( "certificate" )
						                .withDescription( "Certificate" )
						                .hasArg()
						                .withArgName("path")
						                .create() );
		
		options.addOption( OptionBuilder.withLongOpt( "content" )
						                .withDescription( "SOD Content" )
						                .hasArg()
						                .withArgName("path")
						                .create() );		
		
		options.addOption( OptionBuilder.withLongOpt( "out" )
						                .withDescription( "Destination file" )
						                .hasArg()
						                .withArgName("path")
						                .create() );

		return options;
	}


}
