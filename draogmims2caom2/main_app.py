# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2018.                            (c) 2018.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#

import importlib
import logging
import os
import sys
import traceback

from caom2 import Observation, shape, CoordAxis1D, CoordBounds1D, RefCoord
from caom2 import Plane, TemporalWCS, CoordRange1D
from caom2 import Time as caom_Time
from caom2utils import ObsBlueprint, get_gen_proc_arg_parser, gen_proc
from caom2pipe import astro_composable as ac
from caom2pipe import manage_composable as mc
from caom2pipe import execute_composable as ec


__all__ = ['main_app', 'update', 'GMIMSName', 'COLLECTION', 'APPLICATION']


APPLICATION = 'draogmims2caom2'
COLLECTION = 'DRAO'


class GMIMSName(ec.StorageName):
    """DRAO-ST naming rules:
    - support mixed-case file name storage, and mixed-case obs id values
    - support uncompressed files in storage
    """

    GMIMS_NAME_PATTERN = '*'

    def __init__(self, obs_id=None, fname_on_disk=None, file_name=None):
        self.fname_in_ad = file_name
        if obs_id is None:
            if file_name is not None:
                obs_id = file_name.replace('.fits', '')
            else:
                raise mc.CadcException('Expecting to run GMIMS by file names.')
        # TODO - the constructor runs somewhere there is an obs id parameter
        # provided - look into that
        # else:
        #     raise mc.CadcException(
        #         'observation ID {}. Expecting to run GMIMS by file '
        #         'names.'.format(obs_id))

        super(GMIMSName, self).__init__(
            obs_id, COLLECTION, GMIMSName.GMIMS_NAME_PATTERN, fname_on_disk)

    # def get_file_uri(self):
    #     return 'ad:DRAO/drao_60rad.mod.fits'
    @property
    def file_uri(self):
        return 'ad:{}/{}'.format(self.collection, self.file_name)

    def is_valid(self):
        return True


def accumulate_bp(bp, uri):
    """Configure the DRAO-ST-specific ObsBlueprint at the CAOM model Observation
    level."""
    logging.debug('Begin accumulate_bp.')

    bp.set('Observation.observationID', 'test_obs_id')
    bp.set('Observation.proposal.id', 'GMIMS')
    bp.set('Observation.proposal.pi', 'Maik Wolleben')
    bp.set('Observation.proposal.project',
           'Global Magneto-Ionic Medium Survey')
    bp.set('Observation.proposal.title',
           '300 to 900 MHz Rotation Measure Survey')
    bp.set('Observation.proposal.keywords', 'Galactic')

    bp.set('Observation.telescope.name', 'John A. Galt')
    x, y, z = ac.get_location(48.320000, -119.620000, 545.0)
    bp.set('Observation.telescope.geoLocationX', x)
    bp.set('Observation.telescope.geoLocationY', y)
    bp.set('Observation.telescope.geoLocationZ', z)

    bp.set('Observation.instrument.name', 'GMIMS High Frequency Receiver')
    bp.set('Observation.target.name', 'Northern Sky from +87 to -30')

    bp.set('Plane.dataProductType', 'cube')
    bp.set('Plane.calibrationLevel', '4')
    bp.set('Plane.metaRelease', '2030-01-01')
    bp.set('Plane.dataRelease', '2030-01-01')

    bp.configure_position_axes((1, 2))

    logging.debug('Done accumulate_bp.')


def update(observation, **kwargs):
    """Called to fill multiple CAOM model elements and/or attributes, must
    have this signature for import_module loading and execution.

    :param observation A CAOM Observation model instance.
    :param **kwargs Everything else."""
    logging.debug('Begin update.')
    mc.check_param(observation, Observation)

    headers = None
    if 'headers' in kwargs:
        headers = kwargs['headers']
    fqn = None
    if 'fqn' in kwargs:
        fqn = kwargs['fqn']

    # from caom2 import shape, Point, Position
    # # HDU 0 in drao_60rad.mod.fits:
    # SIMPLE  =                    T / conforms to FITS standard
    # BITPIX  =                  -64 / array data type
    # NAXIS   =                    3 / number of array dimensions
    # NAXIS1  =                  720
    # NAXIS2  =                  360
    # NAXIS3  =                  161
    # COMMENT   FITS (Flexible Image Transport System) format is defined in 'Astronomy
    # COMMENT   and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H
    # CTYPE1  = 'GLON-CAR'           / x-axis
    # CTYPE2  = 'GLAT-CAR'           / y-axis
    # CTYPE3  = 'RM      '           / z-axis
    # CRVAL1  =                  0.0 / reference pixel value
    # CRVAL2  =                  0.0 / reference pixel value
    # CRVAL3  =                -400. / reference pixel value
    # CRPIX1  =                360.5 / reference value
    # CRPIX2  =                  181 / reference value
    # CRPIX3  =                   1. / reference value
    # CDELT1  =                 -0.5 / Degrees/pixel
    # CDELT2  =                  0.5 / Degrees/pixel
    # CDELT3  =                   5. / Degrees/pixel
    # CUNIT1  = 'deg     '
    # CUNIT2  = 'deg     '
    # CUNIT3  = 'rad/m2  '

    for ii in observation.planes:
        plane = observation.planes[ii]
        # center = Point(0.0, 0.0)
        # width = 720 * 0.5
        # height = 360 * 0.5
        # plane.position = Position()
        # plane.position.bounds = shape.Box(center, width, height)
        # logging.error('set bounds')
        _update_time(plane)

    logging.debug('Done update.')
    return True


def _update_time(plane):
    logging.debug('Begin _update_time')
    # dates are from the GMIMS paper The Global Magneto-Ionic Survey:
    # Polarimetry of the Southern Sky from 300 to 480 MHz
    #
    survey = [['2009-09-07', '2009-09-21'],
              ['2009-11-30', '2009-12-09'],
              ['2010-02-23', '2010-03-09'],
              ['2010-06-25', '2010-07-08'],
              ['2010-08-26', '2010-09-10'],
              ['2010-11-10', '2010-11-24'],
              ['2011-02-09', '2011-02-23'],
              ['2011-10-20', '2011-11-10'],
              ['2012-02-08', '2012-02-29'],
              ['2012-06-08', '2012-07-02']]
    mc.check_param(plane, Plane)
    samples = []
    for ii in survey:
        start_date = ac.get_datetime(ii[0])
        end_date = ac.get_datetime(ii[1])
        time_bounds = ac.build_plane_time_sample(start_date, end_date)
        samples.append(time_bounds)
    survey_start = ac.get_datetime(survey[0][0])
    survey_end = ac.get_datetime(survey[9][1])
    interval = ac.build_plane_time_interval(survey_start, survey_end, samples)
    plane.time = caom_Time(bounds=interval,
                           dimension=1)
    logging.debug('End _update_time')


def _update_typed_set(typed_set, new_set):
    # remove the previous values
    while len(typed_set) > 0:
        typed_set.pop()
    typed_set.update(new_set)


def _build_blueprints(uri):
    """This application relies on the caom2utils fits2caom2 ObsBlueprint
    definition for mapping FITS file values to CAOM model element
    attributes. This method builds the DRAO-ST blueprint for a single
    artifact.

    The blueprint handles the mapping of values with cardinality of 1:1
    between the blueprint entries and the model attributes.

    :param uri The artifact URI for the file to be processed."""
    module = importlib.import_module(__name__)
    blueprint = ObsBlueprint(module=module)
    accumulate_bp(blueprint, uri)
    blueprints = {uri: blueprint}
    return blueprints


def _get_uri(args):
    result = None
    if args.observation:
        result = GMIMSName(obs_id=args.observation[1]).file_uri
    elif args.local:
        obs_id = GMIMSName.remove_extensions(os.path.basename(args.local[0]))
        result = GMIMSName(obs_id=obs_id).file_uri
    elif args.lineage:
        result = args.lineage[0].split('/', 1)[1]
    else:
        raise mc.CadcException(
            'Could not define uri from these args {}'.format(args))
    return result


def main_app():
    args = get_gen_proc_arg_parser().parse_args()
    try:
        uri = _get_uri(args)
        blueprints = _build_blueprints(uri)
        gen_proc(args, blueprints)
    except Exception as e:
        logging.error('Failed {} execution for {}.'.format(APPLICATION, args))
        tb = traceback.format_exc()
        logging.error(tb)
        sys.exit(-1)

    logging.debug('Done {} processing.'.format(APPLICATION))
