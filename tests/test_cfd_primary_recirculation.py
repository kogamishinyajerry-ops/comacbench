import unittest
import numpy as np

from studies.cfd_primary_recirculation import flux_streamfunction, primary_region, match_root


class PrimaryRecirculationTests(unittest.TestCase):
    def field(self):
        x=np.linspace(0,8,81); y=np.linspace(0,2,41)
        X,Y=np.meshgrid(x,y)
        psi=np.maximum(Y-1,0)+.02*np.maximum(X-5,0)*Y
        inside=(X>0)&(X<5)&(Y>0)&(Y<1)
        psi[inside]=-np.sin(np.pi*X[inside]/5)*np.sin(np.pi*Y[inside])
        psi[(X<.5)&(Y<.25)&(X>0)&(Y>0)]=.001
        psi[1,1]=-.00001
        return x,y,psi

    def test_invalid_geometry_nonfinite_and_path_defect(self):
        x,y,psi=self.field();qx=np.diff(psi,axis=0);qy=-np.diff(psi,axis=1)
        for xx in (x[::-1],np.where(x==1,np.nan,x)):
            with self.assertRaises(ValueError):flux_streamfunction(xx,y,qx,qy)
        bad=qx.copy();bad[3,3]=np.nan
        with self.assertRaises(ValueError):flux_streamfunction(x,y,bad,qy)
        bad=qy.copy();bad[3,3]+=.01
        with self.assertRaises(ValueError):flux_streamfunction(x,y,qx,bad)

    def test_missing_or_multiple_lip_components_rejected(self):
        x,y,psi=self.field()
        with self.assertRaises(ValueError):primary_region(x,y,np.abs(psi))
        bad=psi.copy();bad[19,:]=abs(bad[19,:])+.001;bad[20,1:40]=-.02
        with self.assertRaises(ValueError):primary_region(x,y,bad)

    def test_open_region_and_reference_free_selection(self):
        x,y,psi=self.field()
        bad=psi.copy();bad[1:20,1:]=-.2
        with self.assertRaises(ValueError):primary_region(x,y,bad)
        import inspect
        self.assertEqual(list(inspect.signature(primary_region).parameters),['x','y','psi'])
        labels,region=primary_region(x,y,psi)
        self.assertEqual(region['closed_levels'],[.25,.5,.75])
        self.assertNotEqual(labels[1,1],region['label'])

    def test_corner_root_retained_but_not_selected(self):
        x,y,psi=self.field();labels,region=primary_region(x,y,psi)
        xc=(x[:-1]+x[1:])/2
        shear=xc-5;shear[xc<.5]=.01;shear[0]=-.01
        result=match_root(list(zip(xc.tolist(),shear.tolist())),x,labels,region['label'])
        self.assertEqual(len(result['all_upcrossings']),2)
        self.assertAlmostEqual(result['selected']['x_h'],5)
        self.assertEqual(result['all_upcrossings'][0]['primary_member'],False)
        self.assertEqual(len(result['selected']['bracket']),2)

    def test_zero_plateau_no_crossing_and_multiple_owned_roots_rejected(self):
        x,y,psi=self.field();labels,region=primary_region(x,y,psi)
        xc=(x[:-1]+x[1:])/2;shear=xc-5
        for bad in (np.ones_like(xc),np.zeros_like(xc)):
            with self.assertRaises(ValueError):match_root(list(zip(xc.tolist(),bad.tolist())),x,labels,region['label'])
        shear[10]=1
        with self.assertRaises(ValueError):match_root(list(zip(xc.tolist(),shear.tolist())),x,labels,region['label'])

    def test_flux_reconstruction_uses_both_paths(self):
        x,y,psi=self.field()
        reconstructed,diagnostic=flux_streamfunction(x,y,np.diff(psi,axis=0),-np.diff(psi,axis=1))
        np.testing.assert_allclose(reconstructed,psi,atol=2e-15)
        self.assertLess(diagnostic['path_defect_relative'],1e-12)

    def test_invalid_wall_label_and_coordinates(self):
        x,y,psi=self.field();labels,region=primary_region(x,y,psi)
        xc=(x[:-1]+x[1:])/2;curve=list(zip(xc.tolist(),(xc-5).tolist()))
        for key in (0,-1,999):
            with self.assertRaises(ValueError):match_root(curve,x,labels,key)
        with self.assertRaises(ValueError):match_root(curve[::-1],x,labels,region['label'])
        with self.assertRaises(ValueError):match_root(curve,x+.01,labels,region['label'])

    def test_reference_error_cannot_change_identity(self):
        x,y,psi=self.field();labels,region=primary_region(x,y,psi)
        xc=(x[:-1]+x[1:])/2;curve=list(zip(xc.tolist(),(xc-5).tolist()))
        selected=match_root(curve,x,labels,region['label'])['selected']['x_h']
        errors=[abs(selected-reference)/reference for reference in (.0065,2.922,4.982,50)]
        self.assertEqual(selected,5)
        self.assertEqual(len(set(errors)),4)


if __name__=='__main__':unittest.main()
