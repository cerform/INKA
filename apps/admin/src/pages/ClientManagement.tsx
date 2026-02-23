
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ClientManagement() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Client Management</h1>
            <Card>
                <CardHeader>
                    <CardTitle>Customer CRM</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-500">Client search and history coming soon...</p>
                </CardContent>
            </Card>
        </div>
    );
}
