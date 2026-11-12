// rfacheck.cs - open each .rfa in a folder, report facts, then LoadFamily it into a new project. placeholders __DIR__ (guest folder with .rfa files, flat) __TAG__
using Autodesk.Revit.DB; using System.Linq; using System.IO; using System.Text; using System.Collections.Generic; using System.Globalization;
var app = UIApp.Application; var dir = @"__DIR__"; var outd = @"C:\wl\out\__TAG__"; Directory.CreateDirectory(outd);
var sb = new StringBuilder(); Func<double, string> N = (x) => x.ToString("R", CultureInfo.InvariantCulture);
Func<object, string, object> Prop = (o, n) => { try { var pi = o.GetType().GetProperty(n); return pi == null ? null : pi.GetValue(o, null); } catch { return null; } };
Document proj = null;
var dlgs = new List<string>(); string curName = "";
UIApp.DialogBoxShowing += (sender, e) => { var t = e as Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs; if (t != null) { dlgs.Add("DIALOG\t" + curName + "\t" + t.DialogId + "\t" + (t.Message ?? "").Replace("\n", " ")); try { File.AppendAllText(Path.Combine(outd, "dialogs.txt"), curName + "\t" + t.DialogId + "\t" + (t.Message ?? "").Replace("\n", " ") + "\n"); } catch { } try { t.OverrideResult(1001); } catch { } } else { try { File.AppendAllText(Path.Combine(outd, "dialogs.txt"), curName + "\tnon-task dialog " + e.GetType().Name + "\n"); } catch { } try { e.OverrideResult(1); } catch { } } };
if (__FAILH__) { app.FailuresProcessing += (sender, e) => { try { var fa = e.GetFailuresAccessor(); fa.DeleteAllWarnings(); e.SetProcessingResult(Autodesk.Revit.DB.FailureProcessingResult.Continue); } catch { } }; }
try { proj = app.NewProjectDocument(UnitSystem.Imperial); } catch (Exception ex) { sb.AppendLine("NOPROJECT\t" + ex.Message.Split((char)10)[0]); }
Action fl = () => { try { File.WriteAllText(Path.Combine(outd, "rfacheck.tsv"), sb.ToString() + string.Join("\n", dlgs.ToArray()) + "\n", new UTF8Encoding(false)); } catch { } };      // partial output so a Revit stall still shows how far it got
foreach (var path in Directory.GetFiles(dir, "*.rfa").OrderBy(x => x)) {
  sb.AppendLine("START\t" + Path.GetFileName(path)); fl();
  var name = Path.GetFileName(path); Document d = null; curName = name; int nd0 = dlgs.Count;
  try { d = app.OpenDocumentFile(ModelPathUtils.ConvertUserVisiblePathToModelPath(path), new OpenOptions { Audit = __AUDIT__ }); }
  catch (Exception ex) { sb.AppendLine("OPENFAIL\t" + name + "\t" + ex.GetType().Name + ": " + ex.Message.Split((char)10)[0]); continue; }
  try {
    var f = d.OwnerFamily; sb.AppendLine("OPEN\t" + name + "\tisFam=" + d.IsFamilyDocument + "\tfam=" + (f != null ? f.Name : "null") + "\tcat=" + (d.OwnerFamily != null && d.OwnerFamily.FamilyCategory != null ? d.OwnerFamily.FamilyCategory.Name : "none"));
    fl();
    var fm = d.FamilyManager;
    foreach (FamilyType t in fm.Types) sb.AppendLine("TYPE\t" + name + "\t" + t.Name);
    foreach (FamilyParameter p in fm.Parameters) {
      string dt = ""; try { var gd = p.Definition.GetType().GetMethod("GetDataType"); if (gd != null) dt = Convert.ToString(Prop(gd.Invoke(p.Definition, null), "TypeId")); } catch { }
      sb.AppendLine("PARAM\t" + name + "\t" + p.Definition.Name + "\tinst=" + p.IsInstance + "\tstore=" + p.StorageType + "\tformula=" + (p.Formula ?? "") + "\tshared=" + p.IsShared + "\tdt=" + dt); }
    foreach (FamilyType t in fm.Types) foreach (FamilyParameter p in fm.Parameters) {      // per-type values (2026-11-12): TVAL name type param value
      string v = ""; try { if (t.HasValue(p)) { switch (p.StorageType) { case StorageType.Double: v = t.AsDouble(p).Value.ToString("R"); break; case StorageType.Integer: v = t.AsInteger(p).Value.ToString(); break; case StorageType.String: v = t.AsString(p); break; case StorageType.ElementId: v = "id:" + t.AsElementId(p).IntegerValue; break; } } else v = "(none)"; } catch (Exception) { v = "(err)"; }
      sb.AppendLine("TVAL\t" + name + "\t" + t.Name + "\t" + p.Definition.Name + "\t" + v); }
    var cnt = new SortedDictionary<string, int>();
    foreach (var e in new FilteredElementCollector(d).WhereElementIsNotElementType().ToElements()) { string k = e.GetType().Name; int c; cnt.TryGetValue(k, out c); cnt[k] = c + 1; }
    foreach (var kv in cnt) sb.AppendLine("CNT\t" + name + "\t" + kv.Key + "\t" + kv.Value);
    sb.AppendLine("STAGE\t" + name + "\tcounted"); fl();
    var opt = new Options(); opt.DetailLevel = ViewDetailLevel.Fine; opt.ComputeReferences = false;
    foreach (var gf in new FilteredElementCollector(d).OfClass(typeof(GenericForm)).Cast<GenericForm>()) {
      double vol = 0; int ns = 0; try { foreach (var go in gf.get_Geometry(opt)) { var s = go as Solid; if (s != null && s.Volume > 0) { vol += s.Volume; ns++; } } } catch { }
      BoundingBoxXYZ bb = null; try { bb = gf.get_BoundingBox(null); } catch { }
      sb.AppendLine("FORM\t" + name + "\t" + gf.GetType().Name + "\t" + gf.Id + "\tsolid=" + gf.IsSolid + "\tvol=" + N(vol) + "\tnsolids=" + ns + "\tbbox=" + (bb == null ? "none" : N(bb.Min.X) + "," + N(bb.Min.Y) + "," + N(bb.Min.Z) + ":" + N(bb.Max.X) + "," + N(bb.Max.Y) + "," + N(bb.Max.Z))); }
    foreach (var rp in new FilteredElementCollector(d).OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()) sb.AppendLine("REFPLANE\t" + name + "\t" + rp.Name);
  } catch (Exception ex) { sb.AppendLine("CHECKFAIL\t" + name + "\t" + ex.Message.Split((char)10)[0]); }
  finally { sb.AppendLine("STAGE\t" + name + "\tclosing"); fl(); try { d.Close(false); } catch { } }
  if (proj != null && "__LOAD__" == "1") {
    try { int before = new FilteredElementCollector(proj).OfClass(typeof(Family)).Count(); Family lf = null; bool ok = false; string how = "";
      using (var tx = new Transaction(proj, "load")) { tx.Start(); try { ok = proj.LoadFamily(path, out lf); how = "tx"; } catch (Exception e1) { how = "ex:" + e1.Message.Split((char)10)[0]; } tx.Commit(); }
      if (!ok && lf == null) { try { ok = proj.LoadFamily(path, out lf); how += "|notx"; } catch (Exception e2) { how += "|ex2:" + e2.Message.Split((char)10)[0]; } }
      var fams = new FilteredElementCollector(proj).OfClass(typeof(Family)).Cast<Family>().ToList(); int syms = new FilteredElementCollector(proj).OfClass(typeof(FamilySymbol)).Count();
      sb.AppendLine("LOAD\t" + name + "\tok=" + ok + "\t" + how + "\tfamilies=" + before + "->" + fams.Count + "\tsymbols=" + syms + "\tlf=" + (lf != null ? lf.Name + "/" + lf.GetFamilySymbolIds().Count : "null")); }
    catch (Exception ex) { sb.AppendLine("LOADFAIL\t" + name + "\t" + ex.Message.Split((char)10)[0]); }
  }
}
foreach (var dl in dlgs) sb.AppendLine(dl); File.WriteAllText(Path.Combine(outd, "rfacheck.tsv"), sb.ToString(), new UTF8Encoding(false)); Console.WriteLine("DONE");
