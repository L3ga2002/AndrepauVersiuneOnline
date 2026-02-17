import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatDate } from '../lib/utils';
import { Users, UserPlus, Trash2, Shield, Download, Database, Settings as SettingsIcon } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { token, API_URL, isAdmin, user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // User form
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [userForm, setUserForm] = useState({ username: '', password: '', full_name: '', role: 'casier' });
  const [saving, setSaving] = useState(false);

  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const response = await fetch(`${API_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        setUsers(await response.json());
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token, isAdmin]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!userForm.username || !userForm.password || !userForm.full_name) {
      toast.error('Completați toate câmpurile obligatorii');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(userForm)
      });

      if (response.ok) {
        toast.success('Utilizator creat cu succes');
        setShowUserDialog(false);
        setUserForm({ username: '', password: '', full_name: '', role: 'casier' });
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la creare utilizator');
      }
    } catch (error) {
      toast.error('Eroare la creare utilizator');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Sigur doriți să ștergeți acest utilizator?')) return;

    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Utilizator șters');
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la ștergere');
      }
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handleBackup = async () => {
    try {
      const response = await fetch(`${API_URL}/backup`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `andrepau_backup_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        toast.success('Backup creat cu succes');
      } else {
        toast.error('Eroare la creare backup');
      }
    } catch (error) {
      toast.error('Eroare la creare backup');
    }
  };

  if (!isAdmin) {
    return (
      <div className="p-6" data-testid="settings-page">
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Shield className="w-16 h-16 mb-4 opacity-50" />
            <p>Acces restricționat</p>
            <p className="text-sm mt-2">Această pagină este disponibilă doar pentru administratori</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
          Setări
        </h1>
        <p className="text-muted-foreground mt-1">
          Gestionare utilizatori și configurări sistem
        </p>
      </div>

      <Tabs defaultValue="users" className="space-y-4">
        <TabsList className="bg-secondary">
          <TabsTrigger value="users" data-testid="tab-users" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Users className="w-4 h-4 mr-2" />
            Utilizatori
          </TabsTrigger>
          <TabsTrigger value="backup" data-testid="tab-backup" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Database className="w-4 h-4 mr-2" />
            Backup
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users">
          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-heading text-xl uppercase text-foreground">
                  Gestionare Utilizatori
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Administrare conturi și roluri
                </CardDescription>
              </div>
              <Button
                data-testid="add-user-btn"
                onClick={() => setShowUserDialog(true)}
                className="bg-primary text-primary-foreground"
              >
                <UserPlus className="w-5 h-5 mr-2" />
                Adaugă Utilizator
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="spinner" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-border">
                      <TableHead className="text-muted-foreground">Utilizator</TableHead>
                      <TableHead className="text-muted-foreground">Nume Complet</TableHead>
                      <TableHead className="text-muted-foreground">Rol</TableHead>
                      <TableHead className="text-muted-foreground">Data Creare</TableHead>
                      <TableHead className="text-muted-foreground text-right">Acțiuni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map(u => (
                      <TableRow key={u.id} data-testid={`user-row-${u.id}`} className="border-border">
                        <TableCell className="font-medium text-foreground">{u.username}</TableCell>
                        <TableCell className="text-foreground">{u.full_name}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-sm text-xs uppercase font-medium ${
                            u.role === 'admin' 
                              ? 'bg-primary/20 text-primary' 
                              : 'bg-secondary text-secondary-foreground'
                          }`}>
                            {u.role}
                          </span>
                        </TableCell>
                        <TableCell className="text-muted-foreground">{formatDate(u.created_at)}</TableCell>
                        <TableCell className="text-right">
                          {u.id !== user.id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              data-testid={`delete-user-${u.id}`}
                              onClick={() => handleDeleteUser(u.id)}
                              className="text-destructive hover:bg-destructive/10"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Backup Tab */}
        <TabsContent value="backup">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="font-heading text-xl uppercase text-foreground">
                Backup Bază de Date
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Exportare completă a datelor pentru siguranță
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-6 bg-secondary/30 rounded-sm">
                <div className="flex items-start gap-4">
                  <Database className="w-10 h-10 text-primary" />
                  <div>
                    <h4 className="font-medium text-foreground">Export Complet</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Exportă toate produsele, furnizori, vânzări, NIR-uri și utilizatori într-un fișier JSON.
                    </p>
                    <Button
                      data-testid="create-backup"
                      onClick={handleBackup}
                      className="mt-4 bg-primary text-primary-foreground"
                    >
                      <Download className="w-5 h-5 mr-2" />
                      Descarcă Backup
                    </Button>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-sm">
                <p className="text-sm text-yellow-500">
                  <strong>Recomandare:</strong> Efectuați backup-uri regulate și păstrați-le într-o locație sigură.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create User Dialog */}
      <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
        <DialogContent className="bg-card border-border" data-testid="user-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              Adăugare Utilizator Nou
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <Label className="text-muted-foreground">Username *</Label>
              <Input
                data-testid="input-username"
                value={userForm.username}
                onChange={(e) => setUserForm({...userForm, username: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                required
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Parolă *</Label>
              <Input
                data-testid="input-password"
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                required
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Nume Complet *</Label>
              <Input
                data-testid="input-fullname"
                value={userForm.full_name}
                onChange={(e) => setUserForm({...userForm, full_name: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                required
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Rol</Label>
              <Select 
                value={userForm.role} 
                onValueChange={(v) => setUserForm({...userForm, role: v})}
              >
                <SelectTrigger data-testid="input-role" className="h-12 mt-1 bg-background border-border text-foreground">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="casier">Casier (doar POS)</SelectItem>
                  <SelectItem value="admin">Admin (acces total)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <DialogFooter className="gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowUserDialog(false)}
                className="h-12 px-6 border-border text-foreground"
              >
                Anulează
              </Button>
              <Button
                type="submit"
                data-testid="save-user"
                disabled={saving}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                {saving ? 'Se salvează...' : 'Creează Utilizator'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
